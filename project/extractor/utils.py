from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup, Comment, NavigableString


DROP_TAGS = {
    "script",
    "style",
    "noscript",
    "iframe",
    "svg",
    "canvas",
    "form",
    "select",
    "option",
    "button",
}

ZERO_WIDTH_BOUNDARY_PATTERN = re.compile(r"[\u200b\u2060\ufeff]+")
SPACE_PATTERN = re.compile(r"\s+")
BOOK_CHAPTER_PATTERN = re.compile(r"^/([^/]+)/(\d+)\.htm$")
COMMENTARY_PATTERN = re.compile(r"^/commentaries/([^/]+)/(\d+)(?:-(\d+))?\.htm$")


BOOK_NAMES = {
    "genesis": "Genesis",
    "exodus": "Exodus",
    "leviticus": "Leviticus",
    "numbers": "Numbers",
    "deuteronomy": "Deuteronomy",
    "joshua": "Joshua",
    "judges": "Judges",
    "ruth": "Ruth",
    "1_samuel": "1 Samuel",
    "2_samuel": "2 Samuel",
    "1_kings": "1 Kings",
    "2_kings": "2 Kings",
    "1_chronicles": "1 Chronicles",
    "2_chronicles": "2 Chronicles",
    "ezra": "Ezra",
    "nehemiah": "Nehemiah",
    "esther": "Esther",
    "job": "Job",
    "psalms": "Psalms",
    "proverbs": "Proverbs",
    "ecclesiastes": "Ecclesiastes",
    "songs": "Song of Solomon",
    "isaiah": "Isaiah",
    "jeremiah": "Jeremiah",
    "lamentations": "Lamentations",
    "ezekiel": "Ezekiel",
    "daniel": "Daniel",
    "hosea": "Hosea",
    "joel": "Joel",
    "amos": "Amos",
    "obadiah": "Obadiah",
    "jonah": "Jonah",
    "micah": "Micah",
    "nahum": "Nahum",
    "habakkuk": "Habakkuk",
    "zephaniah": "Zephaniah",
    "haggai": "Haggai",
    "zechariah": "Zechariah",
    "malachi": "Malachi",
    "matthew": "Matthew",
    "mark": "Mark",
    "luke": "Luke",
    "john": "John",
    "acts": "Acts",
    "romans": "Romans",
    "1_corinthians": "1 Corinthians",
    "2_corinthians": "2 Corinthians",
    "galatians": "Galatians",
    "ephesians": "Ephesians",
    "philippians": "Philippians",
    "colossians": "Colossians",
    "1_thessalonians": "1 Thessalonians",
    "2_thessalonians": "2 Thessalonians",
    "1_timothy": "1 Timothy",
    "2_timothy": "2 Timothy",
    "titus": "Titus",
    "philemon": "Philemon",
    "hebrews": "Hebrews",
    "james": "James",
    "1_peter": "1 Peter",
    "2_peter": "2 Peter",
    "1_john": "1 John",
    "2_john": "2 John",
    "3_john": "3 John",
    "jude": "Jude",
    "revelation": "Revelation",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_line(value: str) -> str:
    # BibleHub occasionally contains invisible Unicode boundary characters
    # between visually separated words. Python's \s does not match all of
    # them, so normalize them explicitly before regular whitespace cleanup.
    value = value.replace("\u00ad", "")  # soft hyphen
    value = ZERO_WIDTH_BOUNDARY_PATTERN.sub(" ", value)
    return SPACE_PATTERN.sub(" ", value).strip()


def _is_standalone_link_marker(raw: NavigableString, value: str) -> bool:
    """Return True for one-letter inline link markers such as Bible footnotes.

    Do not remove arbitrary one-letter text: an actual article such as ``a``
    can be meaningful. BibleHub's footnote markers are standalone linked
    lowercase letters, which gives us a much safer signal.
    """
    if re.fullmatch(r"[a-z]", value) is None:
        return False

    parent = raw.parent
    return parent is not None and getattr(parent, "name", None) == "a"


def html_to_lines(html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")

    for tag_name in DROP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    lines: list[str] = []
    previous: str | None = None

    for raw in soup.find_all(string=True):
        if isinstance(raw, Comment):
            continue
        line = normalize_line(str(raw))
        if not line:
            continue
        if isinstance(raw, NavigableString) and _is_standalone_link_marker(raw, line):
            continue
        if line == previous:
            continue
        lines.append(line)
        previous = line

    return lines


def html_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    if soup.title is None:
        return None
    title = normalize_line(soup.title.get_text(" ", strip=True))
    return title or None


def find_line(lines: list[str], patterns: tuple[re.Pattern[str], ...], start: int = 0) -> int | None:
    for index in range(start, len(lines)):
        if any(pattern.search(lines[index]) for pattern in patterns):
            return index
    return None


def trim_at_markers(lines: list[str], markers: tuple[re.Pattern[str], ...]) -> list[str]:
    index = find_line(lines, markers)
    if index is None:
        return lines
    return lines[:index]


def clean_content_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    previous: str | None = None

    for line in lines:
        value = normalize_line(line)
        if not value:
            continue
        if value in {"•", "|", "◄", "►", "Par ▾", "iframe"}:
            continue
        if value == previous:
            continue
        cleaned.append(value)
        previous = value

    return cleaned


def lines_to_text(lines: list[str]) -> str:
    return "\n".join(clean_content_lines(lines)).strip()


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
    slug = Path(urlsplit(url).path).stem
    return slug_to_name(slug)


def place_from_url(url: str) -> str:
    slug = Path(urlsplit(url).path).stem
    return slug_to_name(slug)



TOPICAL_DIRECTORY_PATTERN = re.compile(r"^/topical/[a-z]\.htm$")
ATLAS_DIRECTORY_PATTERN = re.compile(r"^/atlas/[a-z]\.htm$")


def is_discovery_page(url: str) -> bool:
    path = urlsplit(url).path.lower()
    return (
        path == "/topical/"
        or path in {"/topical/naves.htm", "/topical/ttt.htm"}
        or TOPICAL_DIRECTORY_PATTERN.fullmatch(path) is not None
        or path == "/atlas/"
        or ATLAS_DIRECTORY_PATTERN.fullmatch(path) is not None
        or re.fullmatch(r"/(?:" + "|".join(re.escape(slug) for slug in BOOK_NAMES) + r")/(?:index\.htm)?", path) is not None
    )

def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
