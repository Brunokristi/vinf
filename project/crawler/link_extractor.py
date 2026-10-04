from __future__ import annotations

from bs4 import BeautifulSoup

from .url_utils import classify_url, normalize_url


def extract_links(html: str, source_url: str) -> tuple[list[str], int]:
    soup = BeautifulSoup(html, "html.parser")
    eligible: list[str] = []
    seen: set[str] = set()
    total_links = 0

    for anchor in soup.find_all("a", href=True):
        total_links += 1
        normalized = normalize_url(anchor.get("href", ""), source_url)

        if normalized is None or classify_url(normalized) is None:
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        eligible.append(normalized)

    return eligible, total_links
