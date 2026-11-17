"""Embedding re-ranker: re-orders search results by meaning, not just shared words.

Build: uv run python -m dejaview.ranking.reranker --build
Search: uv run python -m dejaview.ranking.reranker "stuck in a time loop"
"""

import argparse
import heapq
import sqlite3

import numpy as np

from dejaview.index.inverted import Index
from dejaview.ranking.bm25 import search as bm25_search

MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_WORDS = 120  # MiniLM reads about 256 word pieces; 120 words stays under that
CANDIDATES = 200
SEMANTIC_WEIGHT = 0.6  # shortcut: hand-picked, tune it on the evaluation set


def chunks(title, text):
    """Plot split into passages, each prefixed with the title, so the end of a long plot is embedded too."""
    words = text.split()
    return [f"{title}. " + " ".join(words[i : i + CHUNK_WORDS]) for i in range(0, max(len(words), 1), CHUNK_WORDS)]


def load_model(progress=False):
    """Text -> unit-length vectors. Imported here because loading torch takes seconds."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL, device="cpu")
    return lambda texts: model.encode(texts, batch_size=64, normalize_embeddings=True, show_progress_bar=progress)


def film_paths(db):
    return [path for (path,) in db.execute("SELECT path FROM films ORDER BY id")]


def build_embeddings(db_path, out_path, encode):
    """Embed every film's plot passages into one file. Returns the passage count."""
    db = sqlite3.connect(db_path)
    texts, owners = [], []
    for doc, title, lead, plot in db.execute("SELECT id, title, lead, plot FROM films ORDER BY id"):
        for passage in chunks(title, plot or lead):
            texts.append(passage)
            owners.append(doc)
    vectors = np.asarray(encode(texts), dtype=np.float16)  # half precision halves the file; ranking is unaffected
    np.savez(out_path, vectors=vectors, owners=np.array(owners, dtype=np.int32), paths=np.array(film_paths(db)))
    return len(texts)


class Reranker:
    def __init__(self, path, db, encode):
        data = np.load(path)
        # film ids are assigned when the parser runs, so embeddings from an older parse point at the wrong films
        if data["paths"].tolist() != film_paths(db):
            raise ValueError(f"{path} is out of date with the films table; rebuild it with --build")
        self.vectors = data["vectors"].astype(np.float32)
        self.owners = data["owners"]
        self.encode = encode

    def similarities(self, query):
        """Array indexed by film id: cosine of the film's best-matching passage; -inf where there is no film."""
        sims = self.vectors @ np.asarray(self.encode([query])[0], dtype=np.float32)
        best = np.full(self.owners.max() + 1, -np.inf, dtype=np.float32)
        np.maximum.at(best, self.owners, sims)
        return best


def hybrid_search(index, reranker, query, k=10):
    """Top k as (film id, score, bm25, semantic), best first.

    Candidates are BM25's top films plus the embeddings' top films, so a description
    sharing no words with the plot can still be found. Score blends BM25 (scaled so the
    best candidate is 1) with cosine similarity.
    """
    sims = reranker.similarities(query)
    keyword = dict(bm25_search(index, query, CANDIDATES))
    dense = np.argsort(-sims)[:CANDIDATES]
    # shortcut: a film found only by embeddings counts as BM25 0 even if it ranked below the cut;
    # score it properly if the evaluation shows that matters
    top = max(keyword.values(), default=0.0) or 1.0
    hits = []
    for doc in set(keyword) | {int(d) for d in dense if np.isfinite(sims[d])}:
        bm25, semantic = keyword.get(doc, 0.0), float(sims[doc])
        hits.append((doc, (1 - SEMANTIC_WEIGHT) * bm25 / top + SEMANTIC_WEIGHT * semantic, bm25, semantic))
    return heapq.nlargest(k, hits, key=lambda hit: (hit[1], -hit[0]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query", nargs="?")
    ap.add_argument("--build", action="store_true", help="embed every film (run after the parser)")
    ap.add_argument("--db", default="data/films.db")
    ap.add_argument("--out", default="data/embeddings.npz")
    args = ap.parse_args()
    if args.build:
        print(f"done: {build_embeddings(args.db, args.out, load_model(progress=True))} passages embedded")
    elif args.query:
        index = Index(args.db)
        reranker = Reranker(args.out, index.db, load_model())
        print("  score   bm25  meaning  film")
        for doc, score, bm25, semantic in hybrid_search(index, reranker, args.query):
            title, year = index.db.execute("SELECT title, year FROM films WHERE id = ?", (doc,)).fetchone()
            print(f"{score:7.3f} {bm25:6.2f} {semantic:8.3f}  {title} ({year})")
    else:
        ap.error("give a query, or --build")
