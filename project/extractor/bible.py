from __future__ import annotations

from .configs.bible import CONFIG, END_PATTERNS, VERSE_SENTINEL
from .engine import matches_any
from .regex_html import html_title, html_to_lines
from .utils import parse_bible_url


def _extract_verses(lines: list[str]) -> list[dict]:
    verses: list[dict] = []
    current_number: int | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_parts
        if current_number is None:
            return
        text = " ".join(current_parts).strip()
        if text:
            verses.append({"verse": current_number, "text": text})
        current_number = None
        current_parts = []

    started = False

    for line in lines:
        if started and matches_any(line, END_PATTERNS):
            break

        marker = VERSE_SENTINEL.fullmatch(line)
        if marker:
            number = int(marker.group(1))
            if number == 1 and not started:
                started = True
            if started and (current_number is None or number == current_number + 1):
                flush()
                current_number = number
                continue

        if started and current_number is not None:
            current_parts.append(line)

    flush()
    return verses


def extract_bible(html: str, url: str) -> dict:
    parsed = parse_bible_url(url)
    if parsed is None:
        raise ValueError(f"Unsupported Bible URL: {url}")

    book, chapter = parsed
    lines = html_to_lines(html, CONFIG)
    verses = _extract_verses(lines)
    text = "\n".join(f"{v['verse']} {v['text']}" for v in verses).strip()

    return {
        "title": f"{book} {chapter}",
        "source_title": html_title(html),
        "book": book,
        "chapter": chapter,
        "verse_count": len(verses),
        "verses": verses,
        "text": text,
    }
