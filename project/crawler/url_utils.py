from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit, urlunsplit


BOOK_SLUGS = {
    "genesis",
    "exodus",
    "leviticus",
    "numbers",
    "deuteronomy",
    "joshua",
    "judges",
    "ruth",
    "1_samuel",
    "2_samuel",
    "1_kings",
    "2_kings",
    "1_chronicles",
    "2_chronicles",
    "ezra",
    "nehemiah",
    "esther",
    "job",
    "psalms",
    "proverbs",
    "ecclesiastes",
    "songs",
    "isaiah",
    "jeremiah",
    "lamentations",
    "ezekiel",
    "daniel",
    "hosea",
    "joel",
    "amos",
    "obadiah",
    "jonah",
    "micah",
    "nahum",
    "habakkuk",
    "zephaniah",
    "haggai",
    "zechariah",
    "malachi",
    "matthew",
    "mark",
    "luke",
    "john",
    "acts",
    "romans",
    "1_corinthians",
    "2_corinthians",
    "galatians",
    "ephesians",
    "philippians",
    "colossians",
    "1_thessalonians",
    "2_thessalonians",
    "1_timothy",
    "2_timothy",
    "titus",
    "philemon",
    "hebrews",
    "james",
    "1_peter",
    "2_peter",
    "1_john",
    "2_john",
    "3_john",
    "jude",
    "revelation",
}

BOOK_RE = "|".join(sorted((re.escape(book) for book in BOOK_SLUGS), key=len, reverse=True))
BIBLE_PATTERN = re.compile(rf"^/(?:{BOOK_RE})/\d+\.htm$")
COMMENTARY_PATTERN = re.compile(rf"^/commentaries/(?:{BOOK_RE})/\d+(?:-\d+)?\.htm$")
TOPICAL_DIRECTORY_PATTERN = re.compile(r"^/topical/[a-z]\.htm$")
TOPICAL_DOCUMENT_PATTERN = re.compile(r"^/topical/[^/]+/[^/]+\.htm$")
ATLAS_DIRECTORY_PATTERN = re.compile(r"^/atlas/[a-z]\.htm$")
ATLAS_DOCUMENT_PATTERN = re.compile(r"^/atlas/[^/]+\.htm$")


def normalize_url(url: str, base_url: str = "https://biblehub.com/") -> str | None:
    absolute = urljoin(base_url, url.strip())
    parsed = urlsplit(absolute)

    if parsed.scheme.lower() not in {"http", "https"}:
        return None

    hostname = (parsed.hostname or "").lower()
    if hostname == "www.biblehub.com":
        hostname = "biblehub.com"

    if hostname != "biblehub.com":
        return None

    path = re.sub(r"/{2,}", "/", parsed.path or "/")

    return urlunsplit(("https", hostname, path, "", ""))


def classify_url(url: str) -> str | None:
    normalized = normalize_url(url)
    if normalized is None:
        return None

    path = urlsplit(normalized).path.lower()

    if BIBLE_PATTERN.fullmatch(path):
        return "bible"

    if COMMENTARY_PATTERN.fullmatch(path):
        return "commentary"

    # Discovery pages are intentionally crawlable: they expose links to actual
    # topical/atlas documents. They are not search documents themselves.
    if path == "/topical/" or TOPICAL_DIRECTORY_PATTERN.fullmatch(path):
        return "topical_index"

    if TOPICAL_DOCUMENT_PATTERN.fullmatch(path):
        return "topical"

    if path == "/atlas/" or ATLAS_DIRECTORY_PATTERN.fullmatch(path):
        return "atlas_index"

    if ATLAS_DOCUMENT_PATTERN.fullmatch(path):
        return "atlas"

    return None


def is_allowed_url(url: str) -> bool:
    return classify_url(url) is not None
