from __future__ import annotations


MIN_TEXT_LENGTH = {
    "bible": 50,
    "commentary": 100,
    "topical": 100,
    "atlas": 100,
}


def validate_document(document: dict) -> list[str]:
    errors: list[str] = []
    document_type = document.get("document_type")
    text = str(document.get("text") or "").strip()

    if not document.get("url"):
        errors.append("missing_url")

    if not document.get("title"):
        errors.append("missing_title")

    if document_type not in MIN_TEXT_LENGTH:
        errors.append("unknown_document_type")
        return errors

    if len(text) < MIN_TEXT_LENGTH[document_type]:
        errors.append("text_too_short")

    if document_type == "bible":
        if not document.get("book"):
            errors.append("missing_book")
        if document.get("chapter") is None:
            errors.append("missing_chapter")
        if not document.get("verses"):
            errors.append("missing_verses")

    if document_type == "commentary" and not document.get("reference"):
        errors.append("missing_reference")

    if document_type == "topical" and not document.get("topic"):
        errors.append("missing_topic")

    if document_type == "atlas" and not document.get("place"):
        errors.append("missing_place")

    return errors
