from __future__ import annotations


# Validation is intentionally category-aware. A legitimate Atlas entry or
# contemporary topical stub can be short, while an empty extraction is still
# rejected by the structural checks below.
MIN_TEXT_LENGTH_BY_GROUP = {
    "bible": 50,
    "commentary": 100,
    "topical": 20,
    "naves": 50,
    "torrey": 50,
    "atlas": 50,
}

MIN_TEXT_LENGTH_BY_TYPE = {
    "bible": 50,
    "commentary": 100,
    "topical": 20,
    "atlas": 50,
}


def _has_text(value: object) -> bool:
    return bool(str(value or "").strip())


def validate_document(document: dict) -> list[str]:
    errors: list[str] = []
    document_type = document.get("document_type")
    crawl_group = document.get("crawl_group")
    text = str(document.get("text") or "").strip()
    sections = document.get("sections") or {}

    if not document.get("url"):
        errors.append("missing_url")

    if not document.get("title"):
        errors.append("missing_title")

    minimum = MIN_TEXT_LENGTH_BY_GROUP.get(
        crawl_group,
        MIN_TEXT_LENGTH_BY_TYPE.get(document_type),
    )

    if minimum is None:
        errors.append("unknown_document_type")
        return errors

    if len(text) < minimum:
        errors.append("text_too_short")

    if document_type == "bible":
        if not document.get("book"):
            errors.append("missing_book")
        if document.get("chapter") is None:
            errors.append("missing_chapter")
        if not document.get("verses"):
            errors.append("missing_verses")

    if document_type == "commentary":
        if not document.get("reference"):
            errors.append("missing_reference")
        if not _has_text(sections.get("commentary")):
            errors.append("missing_commentary_content")

    if document_type == "topical":
        if not document.get("topic"):
            errors.append("missing_topic")
        if not any(
            _has_text(sections.get(name))
            for name in ("article", "naves_index", "torrey_textbook")
        ):
            errors.append("missing_topical_content")

    if document_type == "atlas":
        if not document.get("place"):
            errors.append("missing_place")
        if not any(
            _has_text(sections.get(name))
            for name in ("occurrences", "encyclopedia")
        ):
            errors.append("missing_atlas_content")

    return errors
