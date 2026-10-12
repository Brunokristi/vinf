from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


BOOK_CHAPTER_PATTERN = re.compile(r"^/([^/]+)/(\d+)\.htm$")
COMMENTARY_PATTERN = re.compile(r"^/commentaries/([^/]+)/(\d+)(?:-(\d+))?\.htm$")

BOOK_NAMES = {
    "genesis": "Genesis", "exodus": "Exodus", "leviticus": "Leviticus",
    "numbers": "Numbers", "deuteronomy": "Deuteronomy", "joshua": "Joshua",
    "judges": "Judges", "ruth": "Ruth", "1_samuel": "1 Samuel",
    "2_samuel": "2 Samuel", "1_kings": "1 Kings", "2_kings": "2 Kings",
    "1_chronicles": "1 Chronicles", "2_chronicles": "2 Chronicles",
    "ezra": "Ezra", "nehemiah": "Nehemiah", "esther": "Esther", "job": "Job",
    "psalms": "Psalms", "proverbs": "Proverbs", "ecclesiastes": "Ecclesiastes",
    "songs": "Song of Solomon", "isaiah": "Isaiah", "jeremiah": "Jeremiah",
    "lamentations": "Lamentations", "ezekiel": "Ezekiel", "daniel": "Daniel",
    "hosea": "Hosea", "joel": "Joel", "amos": "Amos", "obadiah": "Obadiah",
    "jonah": "Jonah", "micah": "Micah", "nahum": "Nahum",
    "habakkuk": "Habakkuk", "zephaniah": "Zephaniah", "haggai": "Haggai",
    "zechariah": "Zechariah", "malachi": "Malachi", "matthew": "Matthew",
    "mark": "Mark", "luke": "Luke", "john": "John", "acts": "Acts",
    "romans": "Romans", "1_corinthians": "1 Corinthians",
    "2_corinthians": "2 Corinthians", "galatians": "Galatians",
    "ephesians": "Ephesians", "philippians": "Philippians",
    "colossians": "Colossians", "1_thessalonians": "1 Thessalonians",
    "2_thessalonians": "2 Thessalonians", "1_timothy": "1 Timothy",
    "2_timothy": "2 Timothy", "titus": "Titus", "philemon": "Philemon",
    "hebrews": "Hebrews", "james": "James", "1_peter": "1 Peter",
    "2_peter": "2 Peter", "1_john": "1 John", "2_john": "2 John",
    "3_john": "3 John", "jude": "Jude", "revelation": "Revelation",
}

TOPICAL_DIRECTORY_PATTERN = re.compile(r"^/topical/[a-z]\.htm$")
ATLAS_DIRECTORY_PATTERN = re.compile(r"^/atlas/[a-z]\.htm$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slug_to_name(slug: str) -> str:
    value = unquote(slug).replace("_", " ").replace("-", " ")
    return " ".join(part.capitalize() for part in value.split())


def parse_bible_url(url: str) -> tuple[str, int] | None:
    path = urlsplit(url).path.lower()
    match = BOOK_CHAPTER_PATTERN.fullmatch(path)
    if not match:
        return None
    book_slug, chapter = match.groups()
    return BOOK_NAMES.get(book_slug, slug_to_name(book_slug)), int(chapter)


def parse_commentary_url(url: str) -> tuple[str, int, int | None] | None:
    path = urlsplit(url).path.lower()
    match = COMMENTARY_PATTERN.fullmatch(path)
    if not match:
        return None
    book_slug, chapter, verse = match.groups()
    return (
        BOOK_NAMES.get(book_slug, slug_to_name(book_slug)),
        int(chapter),
        int(verse) if verse is not None else None,
    )


def topic_from_url(url: str) -> str:
    return slug_to_name(Path(urlsplit(url).path).stem)


def place_from_url(url: str) -> str:
    return slug_to_name(Path(urlsplit(url).path).stem)


def crawl_group_from_url(url: str, document_type: str | None = None) -> str | None:
    path = urlsplit(url).path.lower()
    if path.startswith("/topical/naves/"):
        return "naves"
    if path.startswith("/topical/ttt/"):
        return "torrey"
    if path.startswith("/topical/"):
        return "topical"
    if path.startswith("/commentaries/"):
        return "commentary"
    if path.startswith("/atlas/"):
        return "atlas"
    if document_type == "bible" or parse_bible_url(url) is not None:
        return "bible"
    return document_type


def is_discovery_page(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return (
        path == "/topical/"
        or path in {"/topical/naves.htm", "/topical/ttt.htm"}
        or TOPICAL_DIRECTORY_PATTERN.fullmatch(path) is not None
        or path == "/atlas/"
        or ATLAS_DIRECTORY_PATTERN.fullmatch(path) is not None
        or re.fullmatch(
            r"/(?:(?:" + "|".join(re.escape(slug) for slug in BOOK_NAMES) + r"))/(?:index\.htm)?",
            path,
        ) is not None
    )


def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
