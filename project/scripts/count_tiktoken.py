from __future__ import annotations

import json
from pathlib import Path

import tiktoken


DOCUMENTS_FILE = Path("data/processed/documents.jsonl")
ENCODING_NAME = "cl100k_base"


def main() -> None:
    encoding = tiktoken.get_encoding(ENCODING_NAME)

    document_count = 0
    total_tokens = 0
    total_characters = 0

    min_tokens = None
    max_tokens = 0

    with DOCUMENTS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()

            if not line:
                continue

            document = json.loads(line)

            text = document.get("text", "")

            token_count = len(
                encoding.encode(
                    text,
                    disallowed_special=(),
                )
            )

            document_count += 1
            total_tokens += token_count
            total_characters += len(text)

            if min_tokens is None or token_count < min_tokens:
                min_tokens = token_count

            if token_count > max_tokens:
                max_tokens = token_count

            if document_count % 10_000 == 0:
                print(
                    f"Processed {document_count:,} documents, "
                    f"{total_tokens:,} tokens"
                )

    average_tokens = (
        total_tokens / document_count
        if document_count
        else 0
    )

    result = {
        "encoding": ENCODING_NAME,
        "document_count": document_count,
        "total_tokens": total_tokens,
        "average_tokens_per_document": round(
            average_tokens,
            2,
        ),
        "minimum_tokens_per_document": min_tokens or 0,
        "maximum_tokens_per_document": max_tokens,
        "total_characters": total_characters,
    }

    print()
    print(json.dumps(
        result,
        indent=4,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()