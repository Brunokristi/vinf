from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DETAILS_FILE = PROJECT_ROOT / "data" / "metadata" / "ignored_urls.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="Show URLs discovered outside the active crawl scope.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--category", default=None)
    args = parser.parse_args()

    if not DETAILS_FILE.exists():
        print("No ignored URL audit exists yet.")
        return

    shown = 0
    with DETAILS_FILE.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            record = json.loads(line)
            if args.category and record.get("category") != args.category:
                continue

            print(f"URL:      {record.get('url')}")
            print(f"Category: {record.get('category')}")
            print(f"Reason:   {record.get('reason')}")
            print(f"Found on: {record.get('source_url')}")
            print()
            shown += 1
            if shown >= args.limit:
                break

    if shown == 0:
        print("No ignored URLs matched the selected filter.")


if __name__ == "__main__":
    main()
