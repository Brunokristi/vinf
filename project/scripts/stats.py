from __future__ import annotations

from collections import Counter
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_FILE = PROJECT_ROOT / "data" / "metadata" / "pages.jsonl"
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "html"


def main() -> None:
    if not PAGES_FILE.exists():
        print("No pages.jsonl found yet. Run the crawler first.")
        return

    records = []
    with PAGES_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    saved = [record for record in records if record.get("fetch_status") == "saved"]
    types = Counter(record.get("document_type", "unknown") for record in saved)
    total_bytes = sum(path.stat().st_size for path in RAW_DIR.glob("*.html"))

    print(f"Metadata records: {len(records)}")
    print(f"Saved HTML pages: {len(saved)}")
    print(f"Raw HTML size: {total_bytes} bytes ({total_bytes / 1024 / 1024:.2f} MiB)")
    print("Document types:")
    for document_type, count in sorted(types.items()):
        print(f"    {document_type}: {count}")


if __name__ == "__main__":
    main()
