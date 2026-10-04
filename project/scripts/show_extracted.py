from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview extracted search documents.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--preview-chars", type=int, default=700)
    args = parser.parse_args()

    path = Path("data/processed/documents.jsonl")
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
            print(f"DOCUMENT {shown}")
            print("=" * 80)
            print(f"URL:        {document['url']}")
            print(f"Type:       {document['document_type']}")
            print(f"Title:      {document['title']}")
            print(f"Characters: {document['text_length']}")
            print(f"Words:      {document['word_count']}")

            if document["document_type"] == "bible":
                print(f"Book:       {document['book']}")
                print(f"Chapter:    {document['chapter']}")
                print(f"Verses:     {document['verse_count']}")
            elif document["document_type"] == "commentary":
                print(f"Reference:  {document['reference']}")
            elif document["document_type"] == "topical":
                print(f"Topic:      {document['topic']}")
            elif document["document_type"] == "atlas":
                print(f"Place:      {document['place']}")

            preview = document["text"][:args.preview_chars].replace("\n", " ")
            print(f"\nPreview:\n{preview}")
            print()

    if shown == 0:
        print("No valid extracted documents found.")


if __name__ == "__main__":
    main()
