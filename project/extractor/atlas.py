from __future__ import annotations

import re

from .utils import html_title, html_to_lines, lines_to_text, place_from_url


END_MARKERS = (
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)


def extract_atlas(html: str, url: str) -> dict:
    place = place_from_url(url)
    lines = html_to_lines(html)

    occurrences = next(
        (index for index, line in enumerate(lines) if line == "Occurrences"),
        None,
    )
    encyclopedia = next(
        (index for index, line in enumerate(lines) if line == "Encyclopedia"),
        None,
    )

    if occurrences is not None:
        start = occurrences
    elif encyclopedia is not None:
        start = encyclopedia
    else:
        place_index = next(
            (index for index, line in enumerate(lines) if line == place),
            None,
        )
        start = (place_index + 1) if place_index is not None else 0

    end = len(lines)
    for index in range(start, len(lines)):
        if any(pattern.search(lines[index]) for pattern in END_MARKERS):
            end = index
            break

    return {
        "title": place,
        "source_title": html_title(html),
        "place": place,
        "has_occurrences": occurrences is not None,
        "has_encyclopedia": encyclopedia is not None,
        "text": lines_to_text(lines[start:end]),
    }
