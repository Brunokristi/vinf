from __future__ import annotations

from .configs.atlas import CONFIG
from .engine import extract_configured_sections, lines_to_text
from .regex_html import html_title
from .utils import place_from_url


def extract_atlas(html: str, url: str) -> dict:
    place = place_from_url(url)
    sections, lines = extract_configured_sections(html, CONFIG)

    return {
        "title": place,
        "source_title": html_title(html),
        "place": place,
        "has_occurrences": bool(sections.get("occurrences")),
        "has_encyclopedia": bool(sections.get("encyclopedia")),
        "sections": sections,
        "text": lines_to_text(lines),
    }
