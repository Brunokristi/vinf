from __future__ import annotations

import re
import unicodedata

TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)?|\d+", re.UNICODE)


def normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).lower()


def tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(normalize_text(value))
