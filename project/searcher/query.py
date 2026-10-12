from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


WORD_RE = re.compile(r"[A-Za-z0-9']+")


# Intentionally small and explicit.
#
# We do not use NLTK or a huge external stopword list.
# These words carry very little information for our full-text search
# and can otherwise make OR queries match almost the entire corpus.
STOPWORDS = {
    "a",
    "an",
    "the",
    "in",
    "on",
    "at",
    "of",
    "to",
    "for",
    "from",
    "by",
    "with",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
}


@dataclass(frozen=True)
class ParsedQuery:
    original: str
    terms: tuple[str, ...]
    term_counts: Counter[str]
    mode: str
    ignored_stopwords: tuple[str, ...]

    @property
    def display(self) -> str:
        operator = f" {self.mode.upper()} "
        return operator.join(self.terms)


def tokenize(text: str) -> list[str]:
    return [
        match.group(0).lower()
        for match in WORD_RE.finditer(text)
    ]


def parse_query(
    text: str,
    forced_mode: str | None = None,
) -> ParsedQuery:
    raw = text.strip()
    lower = raw.lower()

    has_and = bool(
        re.search(
            r"\s+and\s+",
            lower,
        )
    )

    has_or = bool(
        re.search(
            r"\s+or\s+",
            lower,
        )
    )

    if forced_mode:
        mode = forced_mode.lower()

    elif has_and and not has_or:
        mode = "and"

    elif has_or and not has_and:
        mode = "or"

    else:
        mode = "or"

    # AND / OR are Boolean operators, not terms.
    cleaned = re.sub(
        r"\s+(?:and|or)\s+",
        " ",
        lower,
    )

    raw_terms = tokenize(cleaned)

    ignored_stopwords = [
        term
        for term in raw_terms
        if term in STOPWORDS
    ]

    searchable_terms = [
        term
        for term in raw_terms
        if term not in STOPWORDS
    ]

    if not searchable_terms:
        raise ValueError(
            "Query does not contain any searchable terms "
            "after removing stopwords."
        )

    # Keep duplicate terms for query TF.
    counts = Counter(searchable_terms)

    # Retrieval itself only needs each term once.
    unique_terms = tuple(
        dict.fromkeys(searchable_terms)
    )

    return ParsedQuery(
        original=raw,
        terms=unique_terms,
        term_counts=counts,
        mode=mode,
        ignored_stopwords=tuple(
            dict.fromkeys(ignored_stopwords)
        ),
    )