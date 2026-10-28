from __future__ import annotations

from html import unescape
import re


TITLE_RE = re.compile(
    r"<title>(.*?)</title>",
    re.IGNORECASE | re.DOTALL,
)

NAMESPACE_RE = re.compile(
    r"<ns>(\d+)</ns>",
    re.IGNORECASE,
)

PAGE_ID_RE = re.compile(
    r"<page>.*?<id>(\d+)</id>",
    re.IGNORECASE | re.DOTALL,
)

REDIRECT_RE = re.compile(
    r'<redirect\s+title="([^"]+)"\s*/>',
    re.IGNORECASE,
)

TEXT_RE = re.compile(
    r"<text\b[^>]*>(.*?)</text>",
    re.IGNORECASE | re.DOTALL,
)

CATEGORY_RE = re.compile(
    r"\[\[\s*Category\s*:\s*([^|\]]+)",
    re.IGNORECASE,
)

INTERNAL_LINK_RE = re.compile(
    r"\[\[\s*([^|\]#]+)(?:#[^|\]]*)?(?:\|[^\]]*)?\]\]",
    re.IGNORECASE,
)

COMMENT_RE = re.compile(
    r"<!--.*?-->",
    re.DOTALL,
)

REF_RE = re.compile(
    r"<ref\b[^>]*>.*?</ref\s*>|<ref\b[^>]*/\s*>",
    re.IGNORECASE | re.DOTALL,
)


def normalize_join_key(value: str) -> str:
    value = unescape(value)
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip().lower()


def extract_title(page_xml: str) -> str | None:
    match = TITLE_RE.search(page_xml)

    if not match:
        return None

    return unescape(match.group(1)).strip()


def extract_namespace(page_xml: str) -> int | None:
    match = NAMESPACE_RE.search(page_xml)

    if not match:
        return None

    return int(match.group(1))


def extract_page_id(page_xml: str) -> int | None:
    match = PAGE_ID_RE.search(page_xml)

    if not match:
        return None

    return int(match.group(1))


def extract_redirect(page_xml: str) -> str | None:
    match = REDIRECT_RE.search(page_xml)

    if not match:
        return None

    return unescape(match.group(1)).strip()


def extract_text(page_xml: str) -> str:
    match = TEXT_RE.search(page_xml)

    if not match:
        return ""

    return unescape(match.group(1))


def extract_categories(text: str) -> list[str]:
    categories: list[str] = []
    seen: set[str] = set()

    for match in CATEGORY_RE.finditer(text):
        category = unescape(match.group(1)).strip()

        if not category:
            continue

        key = category.lower()

        if key in seen:
            continue

        seen.add(key)
        categories.append(category)

    return categories


def extract_internal_links(text: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    for match in INTERNAL_LINK_RE.finditer(text):
        target = unescape(match.group(1)).strip()

        if not target:
            continue

        lower = target.lower()

        if lower.startswith(
            (
                "category:",
                "file:",
                "image:",
                "template:",
                "help:",
                "wikipedia:",
            )
        ):
            continue

        key = normalize_join_key(target)

        if key in seen:
            continue

        seen.add(key)
        links.append(target)

    return links


def clean_wikitext_for_preview(text: str) -> str:
    value = COMMENT_RE.sub(" ", text)
    value = REF_RE.sub(" ", value)

    value = re.sub(
        r"\[\[([^|\]]+)\|([^\]]+)\]\]",
        r"\2",
        value,
    )

    value = re.sub(
        r"\[\[([^\]]+)\]\]",
        r"\1",
        value,
    )

    value = re.sub(
        r"\{\{.*?\}\}",
        " ",
        value,
        flags=re.DOTALL,
    )

    value = re.sub(
        r"'{2,5}",
        "",
        value,
    )

    value = re.sub(
        r"<[^>]+>",
        " ",
        value,
    )

    value = re.sub(
        r"\s+",
        " ",
        value,
    )

    return value.strip()


def parse_page(page_xml: str) -> dict | None:
    title = extract_title(page_xml)
    namespace = extract_namespace(page_xml)
    page_id = extract_page_id(page_xml)

    if title is None or namespace is None or page_id is None:
        return None

    text = extract_text(page_xml)
    redirect = extract_redirect(page_xml)

    return {
        "page_id": page_id,
        "title": title,
        "namespace": namespace,
        "redirect": redirect,
        "join_key": normalize_join_key(title),
        "categories": extract_categories(text),
        "internal_links": extract_internal_links(text),
        "text_length": len(text),
        "preview": clean_wikitext_for_preview(text)[:500],
    }