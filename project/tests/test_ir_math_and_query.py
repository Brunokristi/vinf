from __future__ import annotations

import math

import pytest

from indexer.idf import classic_idf, log_tf, smooth_idf
from indexer.tokenizer import tokenize
from searcher.query import parse_query


def test_classic_idf() -> None:
    assert classic_idf(100, 10) == pytest.approx(math.log(10))


def test_smooth_idf() -> None:
    assert smooth_idf(100, 10) == pytest.approx(math.log(101 / 11) + 1)


def test_log_tf() -> None:
    assert log_tf(0) == 0
    assert log_tf(1) == 1
    assert log_tf(4) == pytest.approx(1 + math.log(4))


def test_tokenizer_is_shared_by_index_and_query() -> None:
    assert tokenize("Moses' journey to Egypt") == ["moses", "journey", "to", "egypt"]


def test_query_removes_stopwords() -> None:
    query = parse_query("joseph in egypt")
    assert query.terms == ("joseph", "egypt")
    assert query.ignored_stopwords == ("in",)
    assert query.mode == "or"


def test_query_recognizes_boolean_and() -> None:
    query = parse_query("moses and egypt")
    assert query.terms == ("moses", "egypt")
    assert query.mode == "and"


def test_query_recognizes_boolean_or() -> None:
    query = parse_query("david or solomon")
    assert query.terms == ("david", "solomon")
    assert query.mode == "or"


def test_query_keeps_qtf_for_repeated_terms() -> None:
    query = parse_query("faith faith")
    assert query.terms == ("faith",)
    assert query.term_counts["faith"] == 2


def test_stopword_only_query_is_rejected() -> None:
    with pytest.raises(ValueError):
        parse_query("the in of")
