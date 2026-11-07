from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SearchResult:
    document_id: str
    title: str
    score: float
    crawl_group: str | None = None
    url: str | None = None
    preview: str | None = None
    book: str | None = None
    chapter: int | None = None
    verse: int | None = None
    topic: str | None = None
    place: str | None = None
    wiki_title: str | None = None