from __future__ import annotations

import re
import unicodedata


# Unicode letters (without underscore) with optional apostrophe continuation,
# plus standalone numeric tokens. We deliberately do not stem or lemmatize in
# the first custom index, matching the course checkpoint requirements.
TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)?|\d+", re.UNICODE)


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).lower()


def tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(normalize_text(value))
