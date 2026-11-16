import pytest
from fastapi.testclient import TestClient

from dejaview.api import app as api


@pytest.fixture
def client(films_db, monkeypatch):
    monkeypatch.setenv("DEJAVIEW_DB", str(films_db))
    api.index.cache_clear()
    yield TestClient(api.app)
    api.index.cache_clear()


def test_search_returns_ranked_films(client):
    body = client.get("/search", params={"q": "weatherman relives the same day"}).json()
    top = body["results"][0]
    assert top["title"] == "Groundhog Day" and top["director"] == ["Someone"]
    assert top["snippet"].startswith("A weatherman") and top["score"] > 0
    assert body["query"] == "weatherman relives the same day" and body["took_ms"] >= 0


def test_search_limits_results_and_handles_no_match(client):
    assert len(client.get("/search", params={"q": "robbers", "k": 1}).json()["results"]) == 1
    assert client.get("/search", params={"q": "zzzz"}).json()["results"] == []


@pytest.mark.parametrize("params", [{}, {"q": ""}, {"q": "x" * 201}, {"q": "heist", "k": 0}, {"q": "heist", "k": 51}])
def test_search_rejects_bad_input(client, params):
    assert client.get("/search", params=params).status_code == 422


def test_film_detail_and_missing(client):
    hit = client.get("/search", params={"q": "heat"}).json()["results"][0]
    film = client.get(f"/film/{hit['id']}").json()
    assert film["title"] == "Heat" and "bank heist" in film["plot"]
    assert film["url"].startswith("https://en.wikipedia.org/wiki/")
    assert client.get("/film/9999").status_code == 404
