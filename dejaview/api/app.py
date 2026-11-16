"""HTTP API over the search index.

Run: uv run python -m uvicorn dejaview.api.app:app --reload
"""

import json
import os
import time
from functools import cache

from fastapi import FastAPI, HTTPException, Query

from dejaview.crawler.crawl import BASE
from dejaview.index.inverted import Index
from dejaview.ranking.bm25 import search

app = FastAPI(title="Dejaview")


@cache
def index():
    return Index(os.environ.get("DEJAVIEW_DB", "data/films.db"))


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
async def search_films(q: str = Query(min_length=1, max_length=200), k: int = Query(10, ge=1, le=50)):
    start = time.perf_counter()
    results = []
    for doc, score in search(index(), q, k):
        f = film(doc)
        results.append({"id": doc, "title": f["title"], "year": f["year"], "director": f["director"],
                        "cast": f["cast"], "snippet": (f["plot"] or f["lead"])[:240], "score": round(score, 3)})
    return {"query": q, "results": results, "took_ms": round((time.perf_counter() - start) * 1000, 2)}


@app.get("/film/{doc}")
async def get_film(doc: int):
    f = film(doc)
    if f is None:
        raise HTTPException(404, "No such film")
    return f
