from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_FILE = PROJECT_ROOT / "data" / "metadata" / "pages.jsonl"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Show saved crawl samples for checkpoint documentation.")
    parser.add_argument("--limit", type=int, default=5)
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if not PAGES_FILE.exists():
        print("No pages.jsonl found yet. Run the crawler first.")
        return

    saved = []
    with PAGES_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("fetch_status") == "saved":
                saved.append(record)

    for index, record in enumerate(saved[:args.limit], start=1):
        print(f"Sample {index}")
        print(f"    URL: {record.get('url')}")
        print(f"    Type: {record.get('document_type')}")
        print(f"    Title: {record.get('title')}")
        print(f"    HTTP: {record.get('status_code')}")
        print(f"    Size: {record.get('content_length')} bytes")
        print(f"    Raw HTML: {record.get('raw_html_path')}")
        print()


if __name__ == "__main__":
    main()
