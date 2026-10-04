from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Show failed or invalid extractions.")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    path = Path("data/processed/invalid_documents.jsonl")
    if not path.exists():
        raise SystemExit("Run `python -m extractor` first.")

    shown = 0
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            if shown >= args.limit:
                break
            line = raw_line.strip()
            if not line:
                continue

            document = json.loads(line)
            shown += 1
            print("=" * 80)
            print(f"INVALID {shown}")
            print("=" * 80)
            print(f"URL:    {document.get('url')}")
            print(f"Type:   {document.get('document_type')}")
            print(f"Errors: {', '.join(document.get('validation_errors', []))}")
            if document.get("error"):
                print(f"Error:  {document['error']}")
            if document.get("text"):
                preview = document["text"][:500].replace("\n", " ")
                print(f"Preview:\n{preview}")
            print()

    if shown == 0:
        print("No invalid documents. All extracted pages passed validation.")


if __name__ == "__main__":
    main()
