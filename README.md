# Dejaview

Describe a film you half remember ("guy relives the same day") and find it.

A search engine written from scratch: crawler, inverted index and BM25 ranking,
with embedding re-ranking on top.

## Layout

| Path | Purpose |
|---|---|
| `dejaview/crawler/` | Fetches film pages (robots.txt, rate limit) |
| `dejaview/parser/` | HTML to film records |
| `dejaview/index/` | Tokenizer and inverted index |
| `dejaview/ranking/` | BM25, embedding re-ranker, hybrid score |
| `dejaview/api/` | FastAPI service |
| `web/` | React UI |
| `eval/` | Judged queries, nDCG and latency scripts |
| `tests/` | Unit tests |
| `docs/` | Architecture and decision records |

## Setup

```
uv sync
uv run python -m pytest
```

## Run the pipeline

```
uv run python -m dejaview.crawler.crawl     # fetch film pages into data/pages.db (resumable)
uv run python -m dejaview.parser.parse      # pages -> film records in data/films.db
uv run python -m dejaview.index.inverted    # build the search index
uv run python -m uvicorn dejaview.api.app:app --reload   # API at http://127.0.0.1:8000/docs
npm install --prefix web                    # once
npm run dev --prefix web                    # UI at http://localhost:5173 (needs the API running)
```

Film data from Wikipedia (CC BY-SA). Posters from TMDB.
