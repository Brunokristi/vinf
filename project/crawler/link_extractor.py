from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

from .url_utils import (
    AuditedUrl,
    audit_discovered_url,
    classify_url_details,
    derive_supported_urls,
    normalize_url,
)


@dataclass(frozen=True)
class LinkExtractionResult:
    eligible: list[str]
    derived: list[str]
    ignored: list[AuditedUrl]
    total_links: int


def extract_links_with_audit(html: str, source_url: str) -> LinkExtractionResult:
    soup = BeautifulSoup(html, "html.parser")
    eligible: list[str] = []
    derived: list[str] = []
    ignored: list[AuditedUrl] = []
    seen_eligible: set[str] = set()
    seen_derived: set[str] = set()
    seen_ignored: set[str] = set()
    total_links = 0

    for anchor in soup.find_all("a", href=True):
        total_links += 1
        href = anchor.get("href", "")
        normalized = normalize_url(href, source_url)

        if normalized is not None and classify_url_details(normalized) is not None:
            if normalized not in seen_eligible:
                seen_eligible.add(normalized)
                eligible.append(normalized)
            continue

        for derived_url in derive_supported_urls(href, source_url):
            if derived_url not in seen_eligible:
                seen_eligible.add(derived_url)
                eligible.append(derived_url)
            if derived_url not in seen_derived:
                seen_derived.add(derived_url)
                derived.append(derived_url)

        audited = audit_discovered_url(href, source_url)
        if audited is None or audited.url in seen_ignored:
            continue

        seen_ignored.add(audited.url)
        ignored.append(audited)

    return LinkExtractionResult(
        eligible=eligible,
        derived=derived,
        ignored=ignored,
        total_links=total_links,
    )


def extract_links(html: str, source_url: str) -> tuple[list[str], int]:
    """Backward-compatible helper used by existing tests/scripts."""
    result = extract_links_with_audit(html, source_url)
    return result.eligible, result.total_links
