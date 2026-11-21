"""How often does the right film come back for a vague description? Writes eval/results.md.

Run: uv run python -m eval.evaluate
"""

import json
import statistics
import time
from pathlib import Path

from dejaview.index.inverted import Index
from dejaview.ranking.bm25 import search
from dejaview.ranking.reranker import SEMANTIC_WEIGHT, Reranker, hybrid_search, load_model

HERE = Path(__file__).parent
WEIGHTS = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def rank_of(docs, targets):
    """1-based position of the first target film in a ranked list of film ids, or None."""
    return next((i for i, doc in enumerate(docs, 1) if doc in targets), None)


def summarize(ranks):
    """Hit rates at 1, 3 and 10, and mean reciprocal rank (1 for first place, 1/2 for second, 0 if missed)."""
    n = len(ranks)
    hit = lambda k: sum(r is not None and r <= k for r in ranks) / n
    return {"hit@1": hit(1), "hit@3": hit(3), "hit@10": hit(10), "mrr": sum(1 / r for r in ranks if r) / n}


def timed(fn):
    start = time.perf_counter()
    result = fn()
    return result, (time.perf_counter() - start) * 1000


def main():
    queries = json.loads((HERE / "queries.json").read_text(encoding="utf-8"))
    index = Index("data/films.db")
    rr = Reranker("data/embeddings.npz", index.db, load_model())
    ids = dict(index.db.execute("SELECT path, id FROM films"))
    title = lambda doc: index.db.execute("SELECT title, year FROM films WHERE id = ?", (doc,)).fetchone()
    hybrid_search(index, rr, "warm up")  # first call pays for loading the model

    runs = {"keyword": ([], [])} | {w: ([], []) for w in WEIGHTS}
    misses = []
    for item in queries:
        targets = {ids[p] for p in item["films"]}
        docs, ms = timed(lambda: [d for d, _ in search(index, item["query"], 10)])
        runs["keyword"][0].append(rank_of(docs, targets))
        runs["keyword"][1].append(ms)
        for w in WEIGHTS:
            hits, ms = timed(lambda: hybrid_search(index, rr, item["query"], 10, w))
            runs[w][0].append(rank_of([d for d, *_ in hits], targets))
            runs[w][1].append(ms)
            if w == SEMANTIC_WEIGHT and (runs[w][0][-1] or 99) > 3:
                misses.append((item, runs["keyword"][0][-1], runs[w][0][-1], title(hits[0][0])))

    lines = [f"# Evaluation\n\n{len(queries)} vague descriptions of known films; a hit means the right film is in the top k.\n",
             "| Ranking | Top 1 | Top 3 | Top 10 | MRR | Median ms | Slowest ms |", "|---|---|---|---|---|---|---|"]
    for name, (ranks, ms) in runs.items():
        label = "Keywords only (BM25)" if name == "keyword" else f"Smart, meaning weight {name}"
        label += " (default)" if name == SEMANTIC_WEIGHT else ""
        s = summarize(ranks)
        lines.append(f"| {label} | {s['hit@1']:.0%} | {s['hit@3']:.0%} | {s['hit@10']:.0%} | {s['mrr']:.3f} "
                     f"| {statistics.median(ms):.0f} | {max(ms):.0f} |")
    lines += ["", f"## Misses at the default weight ({SEMANTIC_WEIGHT}): not in the top 3", "",
              "| Query | Keyword rank | Smart rank | Smart's top result |", "|---|---|---|---|"]
    for item, kw, sm, (t, y) in misses:
        lines.append(f"| {item['query']} | {kw or '>10'} | {sm or '>10'} | {t} ({y}) |")
    report = "\n".join(lines) + "\n"
    (HERE / "results.md").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
