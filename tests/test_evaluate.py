import json
from pathlib import Path

import pytest

from eval.evaluate import rank_of, summarize


def test_rank_of_finds_first_target():
    assert rank_of([5, 7, 9], {9, 7}) == 2
    assert rank_of([5, 7], {1}) is None


def test_summarize():
    s = summarize([1, 2, 4, None])
    assert (s["hit@1"], s["hit@3"], s["hit@10"]) == (0.25, 0.5, 0.75)
    assert s["mrr"] == pytest.approx((1 + 1 / 2 + 1 / 4) / 4)


def test_query_file_is_well_formed():
    queries = json.loads((Path(__file__).parent.parent / "eval" / "queries.json").read_text(encoding="utf-8"))
    assert len(queries) == 50
    assert all(q["query"].strip() and q["films"] and all(p.startswith("/wiki/") for p in q["films"]) for q in queries)
    assert len({q["query"] for q in queries}) == 50
