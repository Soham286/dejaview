import pytest

from dejaview.crawler.crawl import Store
from dejaview.index.inverted import build_index
from dejaview.parser.parse import build


def film_html(title, plot):
    return (
        f'<section><table class="infobox"><tr><th class="infobox-above">{title}</th></tr>'
        '<tr><th class="infobox-label">Directed by</th><td class="infobox-data">Someone</td></tr></table>'
        f'<p>{title} is a film.</p></section><section><h2 id="Plot">Plot</h2><p>{plot}</p></section>'
    )


@pytest.fixture
def films_db(tmp_path):
    """Whole pipeline on three tiny pages: store -> parser -> index. Returns the database path."""
    store = Store(tmp_path / "pages.db")
    store.put("/wiki/A", film_html("Groundhog Day", "A weatherman relives the same day again and again."))
    store.put("/wiki/B", film_html("Heat", "A crew of robbers plans a bank heist while a detective hunts them."))
    store.put("/wiki/C", film_html("Day of the Heist", "Robbers argue about lunch."))
    db = tmp_path / "films.db"
    assert build(store, db) == 3
    assert build_index(db) > 0
    return db
