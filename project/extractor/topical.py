from __future__ import annotations

import re

from urllib.parse import urlsplit

from .utils import html_title, html_to_lines, lines_to_text, topic_from_url


START_MARKERS = (
    re.compile(r"^Topical Encyclopedia(?: Introduction)?:?$", re.IGNORECASE),
    re.compile(r"^Introduction:?$", re.IGNORECASE),
)

END_MARKERS = (
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)


def _collection_from_url(url: str) -> str:
    path = urlsplit(url).path.lower()
    if path.startswith("/topical/naves/"):
        return "naves"
    if path.startswith("/topical/ttt/"):
        return "torrey"
    return "contemporary"


def _title_from_html(html: str, fallback: str) -> tuple[str, str | None]:
    source_title = html_title(html)
    if not source_title:
        return fallback, None

    title = re.sub(r"^Topical Bible:\s*", "", source_title, flags=re.IGNORECASE).strip()
    return title or fallback, source_title


def extract_topical(html: str, url: str) -> dict:
    fallback_topic = topic_from_url(url)
    title, source_title = _title_from_html(html, fallback_topic)
    topic = title
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
        "title": title,
        "source_title": source_title,
        "topic": topic,
        "source_collection": _collection_from_url(url),
        "text": lines_to_text(lines[start:end]),
    }
