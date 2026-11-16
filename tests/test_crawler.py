from dejaview.crawler.crawl import BASE, Store, crawl, film_links

LIST_PAGE = """
<table>
<tr><td><i><a href="/wiki/Groundhog_Day_(film)">Groundhog Day</a></i></td>
    <td><a href="/wiki/Bill_Murray">Bill Murray</a></td></tr>
<tr><td><i><a href="/wiki/Mission:_Impossible_(film)#Plot">Mission: Impossible</a></i></td></tr>
<tr><td><i id="x"><a href="https://en.wikipedia.org/wiki/Groundhog_Day_(film)">Groundhog Day</a></i></td></tr>
<tr><td><i><a href="./Groundhog_Day_(film)">Groundhog Day</a></i></td></tr>
<tr><td><i><a href="https://example.com/wiki/Elsewhere">off-site</a></i></td></tr>
<tr><td><i><a href="/w/index.php?title=Lost_Film&amp;redlink=1">Lost Film</a></i></td></tr>
<tr><td><i><a href="/wiki/File:Poster.jpg">poster</a></i></td></tr>
</table>
"""


def test_film_links_keeps_only_italic_article_links():
    assert film_links(LIST_PAGE) == ["/wiki/Groundhog_Day_(film)", "/wiki/Mission:_Impossible_(film)"]


def test_film_links_percent_encodes_non_ascii_once():
    html = '<i><a href="/wiki/El_Niño_(film)">a</a> <a href="/wiki/Am%C3%A9lie">b</a></i>'
    assert film_links(html) == ["/wiki/El_Ni%C3%B1o_(film)", "/wiki/Am%C3%A9lie"]


def test_store_round_trip(tmp_path):
    store = Store(tmp_path / "pages.db")
    assert "/wiki/X" not in store and store.get("/wiki/X") is None
    store.put("/wiki/X", "<p>héllo</p>")
    assert "/wiki/X" in store and store.get("/wiki/X") == "<p>héllo</p>"


def fake_site(calls):
    pages = {BASE + "/wiki/List": LIST_PAGE, BASE + "/wiki/Groundhog_Day_(film)": "<p>film</p>"}

    def fetch(url):
        calls.append(url)
        return pages.get(url)  # None = robots-blocked or failed

    return fetch


def test_crawl_saves_pages_and_resumes(tmp_path):
    store, calls = Store(tmp_path / "pages.db"), []
    assert crawl(["/wiki/List"], store, fake_site(calls)) == 2
    assert store.get("/wiki/Groundhog_Day_(film)") == "<p>film</p>"
    assert "/wiki/Mission:_Impossible_(film)" not in store  # failed fetch is not stored

    calls.clear()
    assert crawl(["/wiki/List"], store, fake_site(calls)) == 0
    assert calls == [BASE + "/wiki/Mission:_Impossible_(film)"]  # only the failed page is retried


def test_crawl_respects_limit(tmp_path):
    store, calls = Store(tmp_path / "pages.db"), []
    assert crawl(["/wiki/List"], store, fake_site(calls), limit=1) == 1
    assert calls == [BASE + "/wiki/List"]
