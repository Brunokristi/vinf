from __future__ import annotations

import re

from .utils import html_title, html_to_lines, lines_to_text, topic_from_url


START_MARKERS = (
    re.compile(r"^Topical Encyclopedia Introduction:?$", re.IGNORECASE),
    re.compile(r"^Introduction:?$", re.IGNORECASE),
)

END_MARKERS = (
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)


def extract_topical(html: str, url: str) -> dict:
    topic = topic_from_url(url)
    lines = html_to_lines(html)

    start = None
    for index, line in enumerate(lines):
        if any(pattern.search(line) for pattern in START_MARKERS):
            start = index + 1
            break

    if start is None:
        title_candidates = {topic, f"Topical Bible: {topic}"}
        title_index = next(
            (index for index, line in enumerate(lines) if line in title_candidates),
            None,
        )
        start = (title_index + 1) if title_index is not None else 0

    end = len(lines)
    for index in range(start, len(lines)):
        if any(pattern.search(lines[index]) for pattern in END_MARKERS):
            end = index
            break

    return {
        "title": topic,
        "source_title": html_title(html),
        "topic": topic,
        "text": lines_to_text(lines[start:end]),
    }
