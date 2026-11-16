import math

import pytest

from dejaview.index.inverted import Index, stem, tokenize
from dejaview.ranking.bm25 import bm25, search


def test_tokenize_lowercases_strips_accents_stopwords_and_plurals():
    assert tokenize("The Núñez Brothers' Heists!") == ["nunez", "brother", "heist"]


@pytest.mark.parametrize(
    "word, expected",
    [("stories", "story"), ("heists", "heist"), ("relives", "relive"), ("glass", "glass"),
     ("virus", "virus"), ("bus", "bus"), ("trees", "trees")],
)
def test_stem(word, expected):
    assert stem(word) == expected


def test_bm25_known_value():
    # idf = ln(1 + 1.5/1.5) = ln 2; the tf part is exactly 1 when tf = 1 and dl = avgdl
    assert bm25(tf=1, df=1, n=2, dl=10, avgdl=10) == pytest.approx(math.log(2))


def test_bm25_prefers_rarer_terms_and_shorter_docs():
    assert bm25(1, df=1, n=100, dl=10, avgdl=10) > bm25(1, df=50, n=100, dl=10, avgdl=10)
    assert bm25(1, df=1, n=100, dl=5, avgdl=10) > bm25(1, df=1, n=100, dl=50, avgdl=10)


@pytest.fixture
def index(films_db):
    return Index(films_db)


def titles(index, query):
    return [index.db.execute("SELECT title FROM films WHERE id = ?", (doc,)).fetchone()[0] for doc, _ in search(index, query)]


def test_search_ranks_matching_films(index):
    assert titles(index, "weatherman reliving the same day")[0] == "Groundhog Day"
    assert titles(index, "bank robbers") == ["Heat", "Day of the Heist"]
    assert titles(index, "heist")[0] == "Day of the Heist"  # title match outranks plot match
    assert titles(index, "zzzz unknown words") == []


def test_postings_round_trip(index):
    assert index.n == 3
    assert sorted(doc for doc, _ in index.postings("robber")) == [2, 3]
    assert index.postings("nosuchterm") == []
