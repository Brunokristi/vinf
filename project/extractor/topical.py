from __future__ import annotations

import re

from .configs.naves import CONFIG as NAVES_CONFIG
from .configs.topical import CONFIG as TOPICAL_CONFIG
from .configs.torrey import CONFIG as TORREY_CONFIG
from .engine import extract_configured_sections, lines_to_text
from .regex_html import html_title
from .utils import crawl_group_from_url, topic_from_url


CONFIG_BY_GROUP = {
    "topical": TOPICAL_CONFIG,
    "naves": NAVES_CONFIG,
    "torrey": TORREY_CONFIG,
}


def _title_from_html(html: str, fallback: str) -> tuple[str, str | None]:
    source_title = html_title(html)
    if not source_title:
        return fallback, None
    title = re.sub(r"^Topical Bible:\s*", "", source_title, flags=re.IGNORECASE).strip()
    return title or fallback, source_title


def extract_topical(html: str, url: str, crawl_group: str | None = None) -> dict:
    group = crawl_group or crawl_group_from_url(url, "topical") or "topical"
    config = CONFIG_BY_GROUP.get(group, TOPICAL_CONFIG)
    fallback = topic_from_url(url)
    title, source_title = _title_from_html(html, fallback)
    sections, lines = extract_configured_sections(html, config)

    return {
        "title": title,
        "source_title": source_title,
        "topic": title,
        "source_collection": "contemporary" if group == "topical" else group,
        "sections": sections,
        "text": lines_to_text(lines),
    }
