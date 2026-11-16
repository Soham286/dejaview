"""Polite Wikipedia film crawler: yearly film-list pages -> film pages -> SQLite.

Run: uv run python -m dejaview.crawler.crawl --from 2020 --to 2020 --limit 5
"""

import argparse
import gzip
import sqlite3
import time
import urllib.error
import urllib.request
import urllib.robotparser
import zlib
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://en.wikipedia.org"
USER_AGENT = "DejaviewBot/0.1 (student search-engine project)"
DELAY = 1.0  # seconds between requests
NAMESPACES = ("File:", "Category:", "Help:", "Wikipedia:", "Template:", "Special:", "Talk:", "Portal:", "Draft:", "User:")


class _FilmLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.italic = 0
        self.links = {}  # dict keeps first-seen order and dedupes

    def handle_starttag(self, tag, attrs):
        if tag == "i":
            self.italic += 1
        elif tag == "a" and self.italic:
            # Wikipedia serves hrefs as /wiki/X, ./X or the absolute URL depending on the renderer
            path = (dict(attrs).get("href") or "").split("#")[0].removeprefix(BASE)
            if path.startswith("./"):
                path = "/wiki/" + path[2:]
            if path.startswith("/wiki/") and not path[6:].startswith(NAMESPACES):
                self.links[path] = None

    def handle_endtag(self, tag):
        if tag == "i" and self.italic:
            self.italic -= 1


def film_links(html):
    """Article paths linked in italics, which is how Wikipedia marks film titles.

    shortcut: italics also catch some books and TV series; the parser drops
    pages without a film infobox.
    """
    p = _FilmLinks()
    p.feed(html)
    return list(p.links)


class Store:
    """Fetched pages, zlib-compressed, keyed by path so a crawl can resume."""

    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS pages (path TEXT PRIMARY KEY, html BLOB NOT NULL,"
            " fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )

    def __contains__(self, path):
        return self.db.execute("SELECT 1 FROM pages WHERE path = ?", (path,)).fetchone() is not None

    def get(self, path):
        row = self.db.execute("SELECT html FROM pages WHERE path = ?", (path,)).fetchone()
        return zlib.decompress(row[0]).decode() if row else None

    def put(self, path, html):
        self.db.execute("INSERT OR REPLACE INTO pages (path, html) VALUES (?, ?)", (path, zlib.compress(html.encode())))
        self.db.commit()


class Fetcher:
    """HTTP GET that obeys robots.txt and waits `delay` seconds between requests."""

    def __init__(self, delay=DELAY):
        self.delay = delay
        self.last = 0.0
        self.robots = urllib.robotparser.RobotFileParser()
        # RobotFileParser.read() would use urllib's default User-Agent, so fetch it ourselves
        self.robots.parse(self._get(BASE + "/robots.txt").splitlines())

    def _get(self, url):
        wait = self.last + self.delay - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
        finally:
            self.last = time.monotonic()
        return body.decode("utf-8", "replace")

    def __call__(self, url):
        """Page HTML, or None if robots.txt forbids it or it cannot be fetched."""
        if not self.robots.can_fetch(USER_AGENT, url):
            return None
        for attempt in range(3):
            try:
                return self._get(url)
            except urllib.error.HTTPError as e:
                if e.code not in (429, 503):
                    return None
                time.sleep(30 * (attempt + 1))  # server asked us to slow down
            except (urllib.error.URLError, TimeoutError):
                time.sleep(5)
        return None


def crawl(seeds, store, fetch, limit=None):
    """Fetch each seed list page and every film it links. Returns pages fetched this run."""
    fetched = 0

    def save(path):
        nonlocal fetched
        html = fetch(BASE + path)
        if html is not None:
            store.put(path, html)
            fetched += 1
        return html

    for seed in seeds:
        if limit is not None and fetched >= limit:
            break
        html = store.get(seed) or save(seed) or ""
        for link in film_links(html):
            if limit is not None and fetched >= limit:
                break
            if link not in store:
                save(link)
        print(f"{seed}: {fetched} pages fetched so far", flush=True)
    return fetched


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--from", dest="start", type=int, default=1970)
    ap.add_argument("--to", dest="end", type=int, default=2025)
    ap.add_argument("--limit", type=int, help="stop after this many fetches")
    ap.add_argument("--db", default="data/pages.db")
    args = ap.parse_args()
    Path(args.db).parent.mkdir(parents=True, exist_ok=True)
    seeds = [f"/wiki/List_of_American_films_of_{y}" for y in range(args.start, args.end + 1)]
    print(f"done: {crawl(seeds, Store(args.db), Fetcher(), args.limit)} pages fetched")
