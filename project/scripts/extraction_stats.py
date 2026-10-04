from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    path = Path("data/processed/extraction_summary.json")
    if not path.exists():
        raise SystemExit("Run `python -m extractor` first.")

    summary = json.loads(path.read_text(encoding="utf-8"))
    print(f"Source pages:      {summary['source_pages']}")
    print(f"Eligible docs:     {summary.get('eligible_documents', summary['valid_documents'] + summary['invalid_documents'])}")
    print(f"Valid documents:   {summary['valid_documents']}")
    print(f"Invalid documents: {summary['invalid_documents']}")
    print(f"Skipped documents: {summary.get('skipped_documents', 0)}")
    print(f"Discovery pages:   {summary.get('skipped_discovery_pages', 0)}")
    print(f"Success rate:      {summary['success_rate_percent']:.2f}%")
    print(f"Text characters:   {summary['total_text_characters']:,}")
    print("\nValid document types:")

    for document_type, count in summary["valid_type_counts"].items():
        print(f"    {document_type}: {count}")

    if summary["validation_error_counts"]:
        print("\nValidation errors:")
        for error, count in summary["validation_error_counts"].items():
            print(f"    {error}: {count}")


if __name__ == "__main__":
    main()
