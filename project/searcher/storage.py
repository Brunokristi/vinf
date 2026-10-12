from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DOC_KEY_FIELDS = (
    "doc_number",
    "doc",
    "doc_id",
    "number",
    "id",
)

DOCUMENT_ID_FIELDS = (
    "document_id",
    "id",
)

NORM_CONTAINERS = (
    "vector_norms",
    "norms",
    "document_norms",
)


def read_json_line_at(path: Path, offset: int) -> dict[str, Any]:
    with path.open("rb") as handle:
        handle.seek(offset)
        line = handle.readline()

    return json.loads(line.decode("utf-8"))


def find_doc_key(record: dict[str, Any]) -> str:
    for field in DOC_KEY_FIELDS:
        if field in record:
            return str(record[field])

    raise KeyError(
        "Could not find document key in catalog record. "
        f"Available keys: {sorted(record.keys())}"
    )


def find_document_id(record: dict[str, Any]) -> str | None:
    for field in DOCUMENT_ID_FIELDS:
        value = record.get(field)

        if value not in (None, ""):
            return str(value)

    return None


def find_norm(record: dict[str, Any], method: str) -> float | None:
    for container in NORM_CONTAINERS:
        value = record.get(container)

        if isinstance(value, dict) and method in value:
            return float(value[method])

    candidates = (
        f"{method}_norm",
        f"norm_{method}",
        f"{method}_document_norm",
        f"document_norm_{method}",
    )

    for field in candidates:
        if field in record:
            return float(record[field])

    return None


class RandomAccessJsonl:
    def __init__(self, path: Path):
        self.path = path
        self._handle = path.open("rb")

    def read(self, offset: int) -> dict[str, Any]:
        self._handle.seek(offset)
        line = self._handle.readline()

        return json.loads(
            line.decode("utf-8")
        )

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "RandomAccessJsonl":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()