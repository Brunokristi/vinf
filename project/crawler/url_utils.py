from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urljoin, urlsplit, urlunsplit

from .url_groups import BIBLE_VERSE_RE, IGNORED_INTERNAL_PATTERNS, URL_GROUPS


@dataclass(frozen=True)
class UrlClassification:
    crawl_group: str
    document_type: str
    is_discovery: bool


@dataclass(frozen=True)
class AuditedUrl:
    url: str
    reason: str
    category: str


def _canonicalize_any_http_url(url: str, base_url: str) -> str | None:
    absolute = urljoin(base_url, url.strip())
    parsed = urlsplit(absolute)

    if parsed.scheme.lower() not in {"http", "https"}:
        return None

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return None

    if hostname == "www.biblehub.com":
        hostname = "biblehub.com"

    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    return urlunsplit(("https", hostname, path, "", ""))


def normalize_url(url: str, base_url: str = "https://biblehub.com/") -> str | None:
    canonical = _canonicalize_any_http_url(url, base_url)
    if canonical is None:
        return None

    parsed = urlsplit(canonical)
    if parsed.hostname != "biblehub.com":
        return None

    return canonical


def classify_url_details(url: str) -> UrlClassification | None:
    normalized = normalize_url(url)
    if normalized is None:
        return None

    path = urlsplit(normalized).path.lower()

    for group in URL_GROUPS:
        # Discovery rules have priority over broad content rules.
        if group.matches_discovery(path):
            return UrlClassification(
                crawl_group=group.name,
                document_type=f"{group.document_type}_index",
                is_discovery=True,
            )

        if group.matches_content(path):
            return UrlClassification(
                crawl_group=group.name,
                document_type=group.document_type,
                is_discovery=False,
            )

    return None


def classify_url(url: str) -> str | None:
    classification = classify_url_details(url)
    return classification.document_type if classification else None


def crawl_group_for_url(url: str) -> str | None:
    classification = classify_url_details(url)
    return classification.crawl_group if classification else None


def is_allowed_url(url: str) -> bool:
    return classify_url_details(url) is not None


def derive_supported_urls(href: str, source_url: str) -> list[str]:
    """Derive in-scope URLs from useful links that are not indexed themselves.

    Bible chapter pages link to per-verse Bible pages such as
    /genesis/1-1.htm. We deliberately do not crawl those duplicate verse pages,
    but they give us the exact URL for the aggregated commentary page.
    """
    canonical = _canonicalize_any_http_url(href, source_url)
    if canonical is None:
        return []

    parsed = urlsplit(canonical)
    if parsed.hostname != "biblehub.com":
        return []

    match = BIBLE_VERSE_RE.fullmatch(parsed.path.lower())
    if match is None:
        return []

    book = match.group("book")
    chapter = match.group("chapter")
    verse = match.group("verse")
    commentary_url = f"https://biblehub.com/commentaries/{book}/{chapter}-{verse}.htm"
    return [commentary_url]


def audit_discovered_url(href: str, source_url: str) -> AuditedUrl | None:
    """Classify a discovered href that is outside the active crawl scope."""
    canonical = _canonicalize_any_http_url(href, source_url)
    if canonical is None:
        return None

    parsed = urlsplit(canonical)
    hostname = parsed.hostname or ""

    if hostname != "biblehub.com":
        return AuditedUrl(
            url=canonical,
            reason="external_domain",
            category=hostname or "external",
        )

    if classify_url_details(canonical) is not None:
        return None

    path = parsed.path.lower()
    for category, reason, pattern in IGNORED_INTERNAL_PATTERNS:
        if pattern.match(path):
            return AuditedUrl(
                url=canonical,
                reason=reason,
                category=category,
            )

    first_segment = next((segment for segment in path.split("/") if segment), "root")
    return AuditedUrl(
        url=canonical,
        reason="unsupported_internal_url",
        category=f"other:{first_segment}",
    )
