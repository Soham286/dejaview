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

Film data from Wikipedia (CC BY-SA). Posters from TMDB.
