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

EXTERNAL_LINK_RE = re.compile(
    r"\[(https?://[^\s\]]+)",
    re.IGNORECASE,
)

SECTION_RE = re.compile(
    r"^={2,6}\s*(.*?)\s*={2,6}\s*$",
    re.MULTILINE,
)

TEMPLATE_RE = re.compile(
    r"\{\{\s*([^|{}\n]+)",
)

INFOBOX_RE = re.compile(
    r"\{\{\s*(Infobox[^|{}\n]*)",
    re.IGNORECASE,
)

BOLD_RE = re.compile(
    r"'''([^']+?)'''",
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

        key = normalize_join_key(category)

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

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        links.append(target)

    return links


def extract_external_links(text: str) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()

    for match in EXTERNAL_LINK_RE.finditer(text):
        url = unescape(match.group(1)).strip()

        if not url:
            continue

        if url in seen:
            continue

        seen.add(url)
        links.append(url)

    return links


def extract_sections(text: str) -> list[str]:
    sections: list[str] = []
    seen: set[str] = set()

    for match in SECTION_RE.finditer(text):
        heading = unescape(match.group(1)).strip()

        if not heading:
            continue

        key = normalize_join_key(heading)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        sections.append(heading)

    return sections


def extract_template_names(text: str) -> list[str]:
    templates: list[str] = []
    seen: set[str] = set()

    for match in TEMPLATE_RE.finditer(text):
        name = unescape(match.group(1)).strip()

        if not name:
            continue

        key = normalize_join_key(name)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        templates.append(name)

    return templates


def extract_infobox_type(text: str) -> str | None:
    match = INFOBOX_RE.search(text)

    if not match:
        return None

    return unescape(
        match.group(1)
    ).strip()


def extract_bold_terms(text: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()

    for match in BOLD_RE.finditer(text):
        term = unescape(match.group(1)).strip()

        if not term:
            continue

        key = normalize_join_key(term)

        if not key:
            continue

        if key in seen:
            continue

        seen.add(key)
        terms.append(term)

    return terms


def count_references(text: str) -> int:
    return sum(
        1
        for _ in REF_RE.finditer(text)
    )


def clean_wikitext_for_preview(text: str) -> str:
    value = COMMENT_RE.sub(
        " ",
        text,
    )

    value = REF_RE.sub(
        " ",
        value,
    )

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
    title = extract_title(
        page_xml,
    )

    namespace = extract_namespace(
        page_xml,
    )

    page_id = extract_page_id(
        page_xml,
    )

    if (
        title is None
        or namespace is None
        or page_id is None
    ):
        return None

    redirect = extract_redirect(
        page_xml,
    )

    text = extract_text(
        page_xml,
    )

    categories = extract_categories(
        text,
    )

    internal_links = extract_internal_links(
        text,
    )

    external_links = extract_external_links(
        text,
    )

    sections = extract_sections(
        text,
    )

    templates = extract_template_names(
        text,
    )

    infobox_type = extract_infobox_type(
        text,
    )

    bold_terms = extract_bold_terms(
        text,
    )

    reference_count = count_references(
        text,
    )

    return {
        "page_id": page_id,
        "title": title,
        "namespace": namespace,
        "redirect": redirect,
        "join_key": normalize_join_key(title),

        "categories": categories,
        "sections": sections,
        "templates": templates,
        "infobox_type": infobox_type,
        "bold_terms": bold_terms,

        "internal_links": internal_links,
        "external_links": external_links,
        "reference_count": reference_count,

        "text_length": len(text),

        "preview": clean_wikitext_for_preview(
            text
        )[:500],
    }