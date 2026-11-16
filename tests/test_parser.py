import json
import sqlite3

from dejaview.crawler.crawl import Store
from dejaview.parser.parse import build, parse_film

# Mirrors the structure Wikipedia actually serves (checked against a crawled page).
FILM = """
<html><head><title>Groundhog Day (film) - Wikipedia</title></head><body>
<h2 class="vector-pinnable-header-label">Contents</h2><p>site chrome, not article text</p>
<section data-mw-section-id="0">
<table class="infobox vevent"><tbody>
<tr><th colspan="2" class="infobox-above summary">Groundhog Day</th></tr>
<tr><th scope="row" class="infobox-label">Directed by</th><td class="infobox-data">
  <style>.plainlist ul{margin:0}</style><a href="/wiki/Harold_Ramis">Harold Ramis</a></td></tr>
<tr><th scope="row" class="infobox-label">Starring</th><td class="infobox-data"><div class="plainlist"><ul>
  <li><a href="/wiki/Bill_Murray">Bill Murray</a></li>
  <li>Andie MacDowell</li></ul></div></td></tr>
<tr><th scope="row" class="infobox-label">Release&nbsp;date</th><td class="infobox-data"><ul>
  <li>February 12, 1993<span style="display:none">(1993-02-12)</span></li></ul></td></tr>
</tbody></table>
<p><i><b>Groundhog Day</b></i> is a 1993 American fantasy comedy film.<sup class="reference"><a href="#cite_note-1">[1]</a></sup></p>
</section>
<section data-mw-section-id="1"><div class="mw-heading"><h2 id="Plot">Plot</h2></div>
<p>Weatherman <a href="/wiki/Phil">Phil Connors</a> relives
the same day.<sup><a href="#n">[b]</a></sup></p>
<p>He &amp; Rita fall in love.</p>
</section>
<section data-mw-section-id="2"><div class="mw-heading"><h2 id="Soundtrack">Soundtrack</h2></div>
<table class="infobox"><tbody>
<tr><th class="infobox-above">Groundhog Day: The Album</th></tr>
<tr><th class="infobox-label">Starring</th><td class="infobox-data">Nobody</td></tr>
</tbody></table>
<p>The album was released later.</p>
</section>
</body></html>
"""

NOT_A_FILM = '<section><table class="infobox"><tr><th class="infobox-above">Bill Murray</th></tr>' \
             '<tr><th class="infobox-label">Born</th><td class="infobox-data">1950</td></tr></table><p>An actor.</p></section>'


def test_parse_film():
    assert parse_film(FILM) == {
        "title": "Groundhog Day",
        "year": 1993,
        "director": ["Harold Ramis"],
        "cast": ["Bill Murray", "Andie MacDowell"],
        "lead": "Groundhog Day is a 1993 American fantasy comedy film.",
        "plot": "Weatherman Phil Connors relives the same day.\nHe & Rita fall in love.",
    }


def test_non_film_page_is_rejected():
    assert parse_film(NOT_A_FILM) is None


def test_build_writes_only_films(tmp_path):
    store = Store(tmp_path / "pages.db")
    store.put("/wiki/Groundhog_Day_(film)", FILM)
    store.put("/wiki/Bill_Murray", NOT_A_FILM)
    out = tmp_path / "films.db"
    assert build(store, out) == 1
    assert build(store, out) == 1  # rebuild replaces, does not duplicate
    rows = sqlite3.connect(out).execute("SELECT path, title, year, starring FROM films").fetchall()
    assert [(p, t, y, json.loads(c)) for p, t, y, c in rows] == [
        ("/wiki/Groundhog_Day_(film)", "Groundhog Day", 1993, ["Bill Murray", "Andie MacDowell"])
    ]
