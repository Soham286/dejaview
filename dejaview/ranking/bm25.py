"""BM25 ranking over the inverted index.

Run: uv run python -m dejaview.ranking.bm25 "guy relives the same day"
"""

import argparse
import heapq
import math
from collections import defaultdict

from dejaview.index.inverted import Index, tokenize

K1 = 1.2  # how quickly repeated terms stop adding score
B = 0.75  # how strongly long documents are penalised


def bm25(tf, df, n, dl, avgdl):
    """Score one term in one document."""
    idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
    return idf * tf * (K1 + 1) / (tf + K1 * (1 - B + B * dl / avgdl))


def search(index, query, k=10):
    """Top k (doc id, score), best first."""
    scores = defaultdict(float)
    for term in set(tokenize(query)):
        postings = index.postings(term)
        for doc, tf in postings:
            scores[doc] += bm25(tf, len(postings), index.n, index.lengths[doc], index.avgdl)
    return heapq.nlargest(k, scores.items(), key=lambda hit: (hit[1], -hit[0]))  # ties: lower id first


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("query")
    ap.add_argument("--db", default="data/films.db")
    args = ap.parse_args()
    index = Index(args.db)
    for doc, score in search(index, args.query):
        title, year = index.db.execute("SELECT title, year FROM films WHERE id = ?", (doc,)).fetchone()
        print(f"{score:6.2f}  {title} ({year})")
