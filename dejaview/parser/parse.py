"""Turn crawled Wikipedia pages into film records in SQLite.

Run: uv run python -m dejaview.parser.parse
"""

import argparse
import json
import re
import sqlite3
from html.parser import HTMLParser

from dejaview.crawler.crawl import Store

SKIP = {"style", "script", "sup"}  # sup = footnote markers like [1]
PLOT_IDS = {"Plot", "Synopsis", "Premise", "Summary", "Plot_summary"}


class _Film(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.sections = 0  # article body is wrapped in <section>; page chrome is not
        self.h2 = None  # id of the current top-level heading; None = lead
        self.capture = None  # "above" | "label" | "data" | "p"
        self.buf = []
        self.label = None
        self.title = None
        self.fields = {}
        self.lead = []
        self.plot = []

    def _start(self, what):
        self.capture, self.buf = what, []

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip += 1
            return
        attrs = dict(attrs)
        cls = attrs.get("class") or ""
        if tag == "section":
            self.sections += 1
        elif tag == "h2" and attrs.get("id"):
            self.h2 = attrs["id"]
        elif tag == "th" and "infobox-above" in cls and self.title is None:
            self._start("above")
        elif tag == "th" and "infobox-label" in cls:
            self._start("label")
        elif tag == "td" and "infobox-data" in cls and self.label:
            self._start("data")
        elif tag == "p" and self.sections and self.capture is None:
            self._start("p")
        elif tag in ("br", "li") and self.capture:
            self.buf.append("\n")  # infobox lists separate items with <br> or <li>

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip = max(0, self.skip - 1)
        elif tag == "section":
            self.sections -= 1
        elif tag == "li" and self.capture:
            self.buf.append("\n")
        elif self.capture and tag == {"above": "th", "label": "th", "data": "td", "p": "p"}[self.capture]:
            raw, what, self.capture = "".join(self.buf), self.capture, None
            text = " ".join(raw.split())
            if what == "above":
                self.title = text
            elif what == "label":
                self.label = text
            elif what == "data":
                items = [" ".join(line.split()) for line in raw.split("\n")]
                # setdefault: a later infobox (e.g. the soundtrack album) must not overwrite the film's
                self.fields.setdefault(self.label, [i for i in items if i])
                self.label = None
            elif text and self.h2 is None:
                self.lead.append(text)
            elif text and self.h2 in PLOT_IDS:
                self.plot.append(text)

    def handle_data(self, data):
        if self.capture and not self.skip:
            self.buf.append(data)


def parse_film(html):
    """Film record as a dict, or None if the page is not a film article."""
    p = _Film()
    p.feed(html)
    f = p.fields
    if "Directed by" not in f or not p.title:
        return None
    dates = " ".join(f.get("Release dates") or f.get("Release date") or [])
    year = re.search(r"\b(?:18|19|20)\d\d\b", dates)
    return {
        "title": p.title,
        "year": int(year.group()) if year else None,
        "director": f["Directed by"],
        "cast": f.get("Starring", []),
        "lead": "\n".join(p.lead),
        "plot": "\n".join(p.plot),
    }


def build(store, out_path):
    """Rebuild the films table from every crawled page. Returns the film count."""
    db = sqlite3.connect(out_path)
    db.execute("DROP TABLE IF EXISTS films")  # derived data: always rebuilt from pages
    db.execute(
        "CREATE TABLE films (id INTEGER PRIMARY KEY, path TEXT UNIQUE NOT NULL, title TEXT NOT NULL,"
        " year INTEGER, director TEXT NOT NULL, starring TEXT NOT NULL, lead TEXT NOT NULL, plot TEXT NOT NULL)"
    )
    n = 0
    for path, html in store.items():
        film = parse_film(html)
        if film:
            db.execute(
                "INSERT INTO films (path, title, year, director, starring, lead, plot) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (path, film["title"], film["year"], json.dumps(film["director"]), json.dumps(film["cast"]),
                 film["lead"], film["plot"]),
            )
            n += 1
    db.commit()
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pages", default="data/pages.db")
    ap.add_argument("--out", default="data/films.db")
    args = ap.parse_args()
    print(f"done: {build(Store(args.pages), args.out)} films")
