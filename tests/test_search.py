import math

import pytest

from dejaview.crawler.crawl import Store
from dejaview.index.inverted import Index, build_index, stem, tokenize
from dejaview.parser.parse import build
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


def film_html(title, plot):
    return (
        f'<section><table class="infobox"><tr><th class="infobox-above">{title}</th></tr>'
        '<tr><th class="infobox-label">Directed by</th><td class="infobox-data">Someone</td></tr></table>'
        f'<p>{title} is a film.</p></section><section><h2 id="Plot">Plot</h2><p>{plot}</p></section>'
    )


@pytest.fixture
def index(tmp_path):
    """Whole pipeline on three tiny pages: store -> parser -> index."""
    store = Store(tmp_path / "pages.db")
    store.put("/wiki/A", film_html("Groundhog Day", "A weatherman relives the same day again and again."))
    store.put("/wiki/B", film_html("Heat", "A crew of robbers plans a bank heist while a detective hunts them."))
    store.put("/wiki/C", film_html("Day of the Heist", "Robbers argue about lunch."))
    db = tmp_path / "films.db"
    assert build(store, db) == 3
    assert build_index(db) > 0
    return Index(db)


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
