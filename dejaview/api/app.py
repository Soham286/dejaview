"""HTTP API over the search index.

Run: uv run python -m uvicorn dejaview.api.app:app --reload
"""

import json
import os
import time
from functools import cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query

from dejaview.crawler.crawl import BASE
from dejaview.index.inverted import Index
from dejaview.ranking.bm25 import search
from dejaview.ranking.reranker import Reranker, hybrid_search, load_model

app = FastAPI(title="Dejaview")


@cache
def index():
    return Index(os.environ.get("DEJAVIEW_DB", "data/films.db"))


@cache
def reranker():
    """The embedding re-ranker, or None if embeddings are missing or stale (search falls back to keywords)."""
    path = Path(os.environ.get("DEJAVIEW_EMB", "data/embeddings.npz"))
    if not path.exists():
        return None
    try:
        return Reranker(path, index().db, load_model())
    except ValueError as e:
        print(f"WARNING: {e}")
        return None


def film(doc):
    row = index().db.execute(
        "SELECT id, path, title, year, director, starring, lead, plot FROM films WHERE id = ?", (doc,)
    ).fetchone()
    if row is None:
        return None
    doc, path, title, year, director, starring, lead, plot = row
    return {"id": doc, "url": BASE + path, "title": title, "year": year, "director": json.loads(director),
            "cast": json.loads(starring), "lead": lead, "plot": plot}


# shortcut: endpoints are async so every query runs on the one event-loop thread and shares the
# SQLite connection; move to a connection per worker thread if one slow query starts blocking others.
@app.get("/search")
async def search_films(
    q: str = Query(min_length=1, max_length=200),
    k: int = Query(10, ge=1, le=50),
    mode: Literal["smart", "keyword"] = "smart",
):
    start = time.perf_counter()
    rr = reranker() if mode == "smart" else None
    if rr:
        hits = hybrid_search(index(), rr, q, k)
    else:
        mode = "keyword"
        hits = [(doc, score, score, None) for doc, score in search(index(), q, k)]
    results = []
    for doc, score, bm25, semantic in hits:
        f = film(doc)
        results.append({"id": doc, "title": f["title"], "year": f["year"], "director": f["director"],
                        "cast": f["cast"], "snippet": (f["plot"] or f["lead"])[:240], "score": round(score, 3),
                        "bm25": round(bm25, 3), "semantic": None if semantic is None else round(semantic, 3)})
    return {"query": q, "mode": mode, "results": results, "took_ms": round((time.perf_counter() - start) * 1000, 2)}


@app.get("/film/{doc}")
async def get_film(doc: int):
    f = film(doc)
    if f is None:
        raise HTTPException(404, "No such film")
    return f
