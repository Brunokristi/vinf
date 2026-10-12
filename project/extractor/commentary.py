from __future__ import annotations

from .configs.commentary import CONFIG
from .engine import extract_configured_sections, lines_to_text
from .regex_html import html_title
from .utils import parse_commentary_url


def extract_commentary(html: str, url: str) -> dict:
    parsed = parse_commentary_url(url)
    if parsed is None:
        raise ValueError(f"Unsupported commentary URL: {url}")

    book, chapter, verse = parsed
    reference = f"{book} {chapter}" if verse is None else f"{book} {chapter}:{verse}"
    sections, lines = extract_configured_sections(html, CONFIG)

    return {
        "title": f"{reference} Commentaries",
        "source_title": html_title(html),
        "book": book,
        "chapter": chapter,
        "verse": verse,
        "reference": reference,
        "sections": sections,
        "text": lines_to_text(lines),
    }
