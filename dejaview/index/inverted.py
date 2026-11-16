"""Tokenizer and inverted index, stored next to the films table.

Run: uv run python -m dejaview.index.inverted
"""

import argparse
import json
import re
import sqlite3
import unicodedata
from array import array
from collections import Counter, defaultdict

STOPWORDS = frozenset(
    "a an and are as at be but by for from has have he her his in is it its not of on or she that the their"
    " them they this to was were which who with s t".split()
)
TITLE_WEIGHT = 3  # shortcut: title boost by repetition, upgrade to per-field BM25F if ranking needs it


def stem(word):
    """Plural stripping only (Harman's S-stemmer).

    shortcut: 'relives' and 'reliving' stay different terms; swap in a Porter
    stemmer if recall on verb forms proves poor in evaluation.
    """
    if len(word) > 3:
        if word.endswith("ies") and not word.endswith(("eies", "aies")):
            return word[:-3] + "y"
        if word.endswith("es"):
            return word if word.endswith(("aes", "ees", "oes")) else word[:-1]
        if word.endswith("s") and not word.endswith(("us", "ss")):
            return word[:-1]
    return word


def tokenize(text):
    # decompose accents then drop the marks, so "Núñez" matches "nunez"
    text = "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))
    return [stem(t) for t in re.findall(r"[a-z0-9]+", text) if t not in STOPWORDS]


def build_index(db_path):
    """Rebuild the index tables from the films table. Returns the number of distinct terms."""
    db = sqlite3.connect(db_path)
    db.executescript(
        "DROP TABLE IF EXISTS terms; DROP TABLE IF EXISTS doc_len;"
        # postings = packed uint32 pairs: doc id, term frequency, doc id, term frequency, ...
        "CREATE TABLE terms (term TEXT PRIMARY KEY, postings BLOB NOT NULL) WITHOUT ROWID;"
        "CREATE TABLE doc_len (id INTEGER PRIMARY KEY, length INTEGER NOT NULL);"
    )
    postings = defaultdict(lambda: array("I"))
    for doc, title, director, starring, lead, plot in db.execute(
        "SELECT id, title, director, starring, lead, plot FROM films ORDER BY id"
    ):
        people = " ".join(json.loads(director) + json.loads(starring))
        tokens = tokenize(" ".join([title] * TITLE_WEIGHT + [lead, plot, people]))
        for term, tf in Counter(tokens).items():
            postings[term].extend((doc, tf))
        db.execute("INSERT INTO doc_len VALUES (?, ?)", (doc, len(tokens)))
    db.executemany("INSERT INTO terms VALUES (?, ?)", ((t, p.tobytes()) for t, p in postings.items()))
    db.commit()
    return len(postings)


class Index:
    """Read side: document lengths in memory, postings read from disk per query term."""

    def __init__(self, db_path):
        self.db = sqlite3.connect(db_path)
        self.lengths = dict(self.db.execute("SELECT id, length FROM doc_len"))
        self.n = len(self.lengths)
        self.avgdl = sum(self.lengths.values()) / self.n if self.n else 0.0

    def postings(self, term):
        """List of (doc id, term frequency) for one term."""
        row = self.db.execute("SELECT postings FROM terms WHERE term = ?", (term,)).fetchone()
        if not row:
            return []
        packed = array("I")
        packed.frombytes(row[0])
        return list(zip(packed[::2], packed[1::2]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default="data/films.db")
    args = ap.parse_args()
    print(f"done: {build_index(args.db)} terms")
