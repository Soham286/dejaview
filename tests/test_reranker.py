import re

import numpy as np
import pytest
from fastapi.testclient import TestClient

from dejaview.api import app as api
from dejaview.crawler.crawl import Store
from dejaview.index.inverted import Index, build_index
from dejaview.parser.parse import build
from dejaview.ranking.bm25 import search
from dejaview.ranking.reranker import Reranker, build_embeddings, chunks, hybrid_search
from tests.conftest import film_html

# Stand-in for the real model: words in the same group count as the same meaning.
CONCEPTS = [{"loop", "relives", "repeat", "day"}, {"heist", "robbers", "bank", "steal"}, {"lunch", "food"}]


def fake_encode(texts):
    out = np.zeros((len(texts), len(CONCEPTS) + 1), dtype=np.float32)
    for i, text in enumerate(texts):
        words = set(re.findall(r"[a-z]+", text.lower()))
        out[i, :-1] = [len(words & group) for group in CONCEPTS]
        out[i, -1] = 0.1  # keeps every vector non-zero
        out[i] /= np.linalg.norm(out[i])
    return out


@pytest.fixture
def reranked(films_db, tmp_path):
    path = tmp_path / "embeddings.npz"
    assert build_embeddings(films_db, path, fake_encode) == 3
    index = Index(films_db)
    return index, Reranker(path, index.db, fake_encode), path


def title(index, doc):
    return index.db.execute("SELECT title FROM films WHERE id = ?", (doc,)).fetchone()[0]


def test_chunks_cover_the_whole_plot():
    passages = chunks("T", " ".join(map(str, range(250))))
    assert len(passages) == 3 and passages[2] == "T. " + " ".join(map(str, range(240, 250)))
    assert chunks("T", "") == ["T. "]


def test_finds_film_that_shares_no_words_with_the_query(reranked):
    index, rr, _ = reranked
    assert search(index, "caught in a time loop") == []  # keywords alone find nothing
    doc, _, bm25, semantic = hybrid_search(index, rr, "caught in a time loop")[0]
    assert title(index, doc) == "Groundhog Day" and bm25 == 0 and semantic > 0.5


def test_blends_keyword_and_meaning_scores(reranked):
    index, rr, _ = reranked
    hits = hybrid_search(index, rr, "bank robbers")
    assert [title(index, d) for d, *_ in hits][:2] == ["Heat", "Day of the Heist"]
    assert all(bm25 > 0 and semantic > 0 for _, _, bm25, semantic in hits[:2])
    assert hits == sorted(hits, key=lambda h: -h[1])


def test_stale_embeddings_are_rejected(reranked, tmp_path):
    index, _, path = reranked
    store = Store(tmp_path / "pages2.db")
    store.put("/wiki/Z", film_html("Alien", "A crew meets a monster."))
    db = tmp_path / "films2.db"
    build(store, db)
    build_index(db)
    with pytest.raises(ValueError, match="out of date"):
        Reranker(path, Index(db).db, fake_encode)


@pytest.fixture
def client(reranked, films_db, monkeypatch):
    _, _, path = reranked
    monkeypatch.setenv("DEJAVIEW_DB", str(films_db))
    monkeypatch.setenv("DEJAVIEW_EMB", str(path))
    monkeypatch.setattr(api, "load_model", lambda: fake_encode)
    api.index.cache_clear()
    api.reranker.cache_clear()
    yield TestClient(api.app)
    api.index.cache_clear()
    api.reranker.cache_clear()


def test_api_smart_and_keyword_modes(client):
    smart = client.get("/search", params={"q": "caught in a time loop"}).json()
    assert smart["mode"] == "smart" and smart["results"][0]["title"] == "Groundhog Day"
    assert smart["results"][0]["semantic"] > 0.5 and smart["results"][0]["bm25"] == 0
    keyword = client.get("/search", params={"q": "bank robbers", "mode": "keyword"}).json()
    assert keyword["mode"] == "keyword" and keyword["results"][0]["semantic"] is None
    assert client.get("/search", params={"q": "x", "mode": "magic"}).status_code == 422


def test_api_falls_back_to_keywords_without_embeddings(client, monkeypatch):
    monkeypatch.setenv("DEJAVIEW_EMB", "does/not/exist.npz")
    api.reranker.cache_clear()
    body = client.get("/search", params={"q": "bank robbers"}).json()
    assert body["mode"] == "keyword" and body["results"][0]["title"] == "Heat"
