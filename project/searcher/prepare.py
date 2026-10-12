from __future__ import annotations

import json
from pathlib import Path

from .storage import find_doc_key, find_document_id, find_norm


INDEX_DIR = Path("data/index")
INDEX_FILE = INDEX_DIR / "index.jsonl"
CATALOG_FILE = INDEX_DIR / "documents.jsonl"
SOURCE_FILE = Path("data/processed/documents.jsonl")

LEXICON_FILE = INDEX_DIR / "lexicon.json"
CATALOG_OFFSETS_FILE = INDEX_DIR / "catalog_offsets.json"
SOURCE_OFFSETS_FILE = INDEX_DIR / "source_offsets.json"
NORMS_FILE = INDEX_DIR / "document_norms.json"
ASSETS_FILE = INDEX_DIR / "search_assets.json"


def source_signature(path: Path) -> dict:
    stat = path.stat()
    return {
        "path": str(path),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def build_lexicon() -> dict[str, dict]:
    lexicon: dict[str, dict] = {}

    with INDEX_FILE.open("rb") as handle:
        while True:
            offset = handle.tell()
            line = handle.readline()

            if not line:
                break

            record = json.loads(line.decode("utf-8"))
            term = record.get("term")

            if term is None:
                raise KeyError(
                    "index.jsonl record does not contain 'term'. "
                    f"Keys: {sorted(record.keys())}"
                )

            df = record.get("df")

            if df is None:
                postings = record.get("postings", [])
                df = len(postings)

            lexicon[str(term)] = {
                "offset": offset,
                "df": int(df),
            }

    return lexicon


def build_catalog_assets() -> tuple[dict[str, int], dict[str, dict], dict[str, str]]:
    offsets: dict[str, int] = {}
    norms: dict[str, dict] = {}
    doc_to_document_id: dict[str, str] = {}

    missing_norms = []

    with CATALOG_FILE.open("rb") as handle:
        while True:
            offset = handle.tell()
            line = handle.readline()

            if not line:
                break

            record = json.loads(line.decode("utf-8"))
            doc_key = find_doc_key(record)

            classic = find_norm(record, "classic")
            smooth = find_norm(record, "smooth")

            if classic is None or smooth is None:
                if len(missing_norms) < 5:
                    missing_norms.append(
                        {
                            "doc": doc_key,
                            "keys": sorted(record.keys()),
                        }
                    )
            else:
                norms[doc_key] = {
                    "classic": classic,
                    "smooth": smooth,
                }

            document_id = find_document_id(record)
            if document_id:
                doc_to_document_id[doc_key] = document_id

            offsets[doc_key] = offset

    if missing_norms:
        raise RuntimeError(
            "Could not find classic/smooth document norms in data/index/documents.jsonl.\n"
            "The current searcher already uses document norms, but this patch could not "
            "recognize their field names.\n"
            f"Example records: {json.dumps(missing_norms, indent=4)}"
        )

    return offsets, norms, doc_to_document_id


def build_source_offsets() -> dict[str, int]:
    offsets: dict[str, int] = {}

    with SOURCE_FILE.open("rb") as handle:
        while True:
            offset = handle.tell()
            line = handle.readline()

            if not line:
                break

            record = json.loads(line.decode("utf-8"))
            document_id = record.get("document_id")

            if document_id is None:
                raise KeyError(
                    "data/processed/documents.jsonl record has no document_id. "
                    f"Keys: {sorted(record.keys())}"
                )

            offsets[str(document_id)] = offset

    return offsets


def main() -> None:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    print("Building lexicon offsets...")
    lexicon = build_lexicon()

    print("Building catalog offsets and norm cache...")
    catalog_offsets, norms, doc_to_document_id = build_catalog_assets()

    print("Building extracted-document offsets...")
    source_offsets = build_source_offsets()

    assets = {
        "version": 1,
        "document_count": len(catalog_offsets),
        "vocabulary_size": len(lexicon),
        "sources": {
            "index": source_signature(INDEX_FILE),
            "catalog": source_signature(CATALOG_FILE),
            "processed": source_signature(SOURCE_FILE),
        },
        "files": {
            "lexicon": str(LEXICON_FILE),
            "catalog_offsets": str(CATALOG_OFFSETS_FILE),
            "source_offsets": str(SOURCE_OFFSETS_FILE),
            "document_norms": str(NORMS_FILE),
        },
    }

    LEXICON_FILE.write_text(
        json.dumps(lexicon, ensure_ascii=False),
        encoding="utf-8",
    )
    CATALOG_OFFSETS_FILE.write_text(
        json.dumps(
            {
                "offsets": catalog_offsets,
                "doc_to_document_id": doc_to_document_id,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    SOURCE_OFFSETS_FILE.write_text(
        json.dumps(source_offsets, ensure_ascii=False),
        encoding="utf-8",
    )
    NORMS_FILE.write_text(
        json.dumps(norms, ensure_ascii=False),
        encoding="utf-8",
    )
    ASSETS_FILE.write_text(
        json.dumps(assets, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print(json.dumps(assets, indent=4, ensure_ascii=False))
    print()
    print("Search assets ready.")


if __name__ == "__main__":
    main()
