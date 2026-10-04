from __future__ import annotations

import re

from .utils import html_title, html_to_lines, lines_to_text, parse_commentary_url


START_MARKERS = (
    re.compile(r"^EXPOSITORY \(ENGLISH BIBLE\)$", re.IGNORECASE),
    re.compile(r"Commentary for English Readers", re.IGNORECASE),
    re.compile(r"\bCommentary\b", re.IGNORECASE),
)

END_MARKERS = (
    re.compile(r"^Parallel Commentaries", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)


def _content_bounds(lines: list[str], reference: str) -> tuple[int, int]:
    jump_index = next(
        (index for index, line in enumerate(lines) if line.startswith("Jump to:")),
        None,
    )
    search_from = (jump_index + 1) if jump_index is not None else 0

    start = None
    for index in range(search_from, len(lines)):
        line = lines[index]
        if line == reference:
            continue
        if any(pattern.search(line) for pattern in START_MARKERS):
            start = index
            break

    if start is None:
        start = search_from

    end = len(lines)
    for index in range(start + 1, len(lines)):
        if any(pattern.search(lines[index]) for pattern in END_MARKERS):
            end = index
            break

    return start, end


def extract_commentary(html: str, url: str) -> dict:
    parsed = parse_commentary_url(url)
    if parsed is None:
        raise ValueError(f"Unsupported commentary URL: {url}")

    book, chapter, verse = parsed
    reference = f"{book} {chapter}" if verse is None else f"{book} {chapter}:{verse}"
    lines = html_to_lines(html)
    start, end = _content_bounds(lines, reference)
    text = lines_to_text(lines[start:end])

    return {
        "title": f"{reference} Commentaries",
        "source_title": html_title(html),
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "reference": reference,
        "text": text,
    }
