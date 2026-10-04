from __future__ import annotations

import re

from .utils import html_title, html_to_lines, lines_to_text, parse_bible_url


END_MARKERS = (
    re.compile(r"^Footnotes:?$", re.IGNORECASE),
    re.compile(r"^Berean Standard Bible \(BSB\)", re.IGNORECASE),
)
VERSE_NUMBER = re.compile(r"^(\d{1,3})$")


def _find_first_verse(lines: list[str]) -> int | None:
    for index, line in enumerate(lines[:-1]):
        if line != "1":
            continue

        for lookahead in range(index + 1, min(index + 5, len(lines))):
            candidate = lines[lookahead]
            if len(candidate) >= 8 and not VERSE_NUMBER.fullmatch(candidate):
                return index

    return None


def _find_end(lines: list[str], start: int) -> int:
    for index in range(start, len(lines)):
        if any(pattern.search(lines[index]) for pattern in END_MARKERS):
            return index
    return len(lines)


def _extract_verses(lines: list[str]) -> list[dict]:
    verses: list[dict] = []
    current_number: int | None = None
    current_parts: list[str] = []

    def flush() -> None:
        nonlocal current_number, current_parts
        if current_number is None:
            return
        text = lines_to_text(current_parts)
        if text:
            verses.append({"verse": current_number, "text": text})
        current_number = None
        current_parts = []

    for line in lines:
        match = VERSE_NUMBER.fullmatch(line)
        if match:
            number = int(match.group(1))
            if current_number is None or number == current_number + 1:
                flush()
                current_number = number
                continue

        if current_number is not None:
            current_parts.append(line)

    flush()
    return verses


def extract_bible(html: str, url: str) -> dict:
    parsed = parse_bible_url(url)
    if parsed is None:
        raise ValueError(f"Unsupported Bible URL: {url}")

    book, chapter = parsed
    lines = html_to_lines(html)
    start = _find_first_verse(lines)

    if start is None:
        text = ""
        verses: list[dict] = []
    else:
        end = _find_end(lines, start)
        verses = _extract_verses(lines[start:end])
        text = "\n".join(
            f"{verse['verse']} {verse['text']}" for verse in verses
        ).strip()

    return {
        "title": f"{book} {chapter}",
        "source_title": html_title(html),
        "book": book,
        "chapter": chapter,
        "verse_count": len(verses),
        "verses": verses,
        "text": text,
    }
