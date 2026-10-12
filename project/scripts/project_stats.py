from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw" / "html"
PAGES_FILE = DATA_DIR / "metadata" / "pages.jsonl"
EXTRACTION_SUMMARY = DATA_DIR / "processed" / "extraction_summary.json"
INDEX_STATS = DATA_DIR / "index" / "stats.json"
SEEN_FILE = DATA_DIR / "state" / "seen_urls.txt"
VISITED_FILE = DATA_DIR / "state" / "visited_urls.txt"


def count_nonempty_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for line in handle if line.strip())


def directory_size(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(file.stat().st_size for file in path.rglob("*") if file.is_file())


def human_bytes(value: int) -> str:
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{value} B"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    raw_files = list(RAW_DIR.glob("*.html")) if RAW_DIR.exists() else []
    raw_size = sum(path.stat().st_size for path in raw_files)
    extraction = load_json(EXTRACTION_SUMMARY)
    index = load_json(INDEX_STATS)

    print("Biblical Search Engine — project statistics")
    print("=" * 52)
    print()
    print("CRAWL")
    print(f"Metadata records:       {count_nonempty_lines(PAGES_FILE):,}")
    print(f"Saved raw HTML files:   {len(raw_files):,}")
    print(f"Raw HTML size:          {human_bytes(raw_size)}")
    print(f"Seen URLs:              {count_nonempty_lines(SEEN_FILE):,}")
    print(f"Visited URLs:           {count_nonempty_lines(VISITED_FILE):,}")

    print()
    print("EXTRACTION")
    if extraction:
        print(f"Source pages:           {extraction.get('source_pages', 0):,}")
        print(f"Valid documents:        {extraction.get('valid_documents', 0):,}")
        print(f"Invalid documents:      {extraction.get('invalid_documents', 0):,}")
        print(f"Skipped documents:      {extraction.get('skipped_documents', 0):,}")
        print(f"Text characters:        {extraction.get('total_text_characters', 0):,}")
        print("Valid groups:")
        for group, count in extraction.get("valid_group_counts", {}).items():
            print(f"    {group:12s} {count:,}")
    else:
        print("No extraction summary found.")

    print()
    print("INDEX")
    if index:
        print(f"Documents:              {index.get('document_count', 0):,}")
        print(f"Vocabulary:             {index.get('vocabulary_size', 0):,}")
        print(f"Posting entries:        {index.get('posting_count', 0):,}")
        print(f"Indexer tokens:         {index.get('total_tokens', 0):,}")
        print(f"Avg tokens/document:    {index.get('average_document_tokens', 0)}")
        print(f"IDF methods:            {', '.join(index.get('idf_methods', []))}")
        print(f"TF method:              {index.get('tf_method', '-')}")
    else:
        print("No index statistics found.")

    print()
    print("DISK")
    print(f"data/raw:               {human_bytes(directory_size(DATA_DIR / 'raw'))}")
    print(f"data/processed:         {human_bytes(directory_size(DATA_DIR / 'processed'))}")
    print(f"data/index:             {human_bytes(directory_size(DATA_DIR / 'index'))}")


if __name__ == "__main__":
    main()
