from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from indexer.tokenizer import tokenize


# Intentionally small and explicit. Stopwords are removed only from the query;
# the inverted index itself remains complete and reproducible.
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


def parse_query(text: str, forced_mode: str | None = None) -> ParsedQuery:
    raw = text.strip()
    lower = raw.lower()

    has_and = bool(re.search(r"\s+and\s+", lower))
    has_or = bool(re.search(r"\s+or\s+", lower))

    if forced_mode:
        mode = forced_mode.lower()
    elif has_and and not has_or:
        mode = "and"
    elif has_or and not has_and:
        mode = "or"
    else:
        mode = "or"

    # AND / OR are Boolean operators, not index terms.
    cleaned = re.sub(r"\s+(?:and|or)\s+", " ", lower)
    raw_terms = tokenize(cleaned)

    ignored_stopwords = [term for term in raw_terms if term in STOPWORDS]
    searchable_terms = [term for term in raw_terms if term not in STOPWORDS]

    if not searchable_terms:
        raise ValueError(
            "Query does not contain any searchable terms after removing stopwords."
        )

    counts = Counter(searchable_terms)
    unique_terms = tuple(dict.fromkeys(searchable_terms))

    return ParsedQuery(
        original=raw,
        terms=unique_terms,
        term_counts=counts,
        mode=mode,
        ignored_stopwords=tuple(dict.fromkeys(ignored_stopwords)),
    )
