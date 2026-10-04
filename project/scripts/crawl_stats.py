from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SUMMARY_FILE = PROJECT_ROOT / "data" / "metadata" / "run_summary.json"


def main() -> None:
    if not SUMMARY_FILE.exists():
        print("No crawl summary exists yet.")
        return

    summary = json.loads(SUMMARY_FILE.read_text(encoding="utf-8"))

    print(f"Pages saved:        {summary.get('pages_saved', 0)}")
    print(f"New URLs found:     {summary.get('new_urls_discovered', 0)}")
    print(f"Derived URLs found: {summary.get('new_derived_urls_discovered', 0)}")
    print(f"Ignored URLs found: {summary.get('new_ignored_urls_discovered', 0)}")
    print(f"Frontier remaining: {summary.get('frontier_remaining', 0)}")
    print()

    print("Saved by crawl group:")
    for group, count in summary.get("saved_by_group", {}).items():
        print(f"    {group}: {count}")

    print("\nFrontier by crawl group:")
    for group, count in summary.get("frontier_by_group", {}).items():
        print(f"    {group}: {count}")

    ignored = summary.get("ignored_urls", {})
    print(f"\nIgnored URLs total: {ignored.get('ignored_urls_total', 0)}")
    print("Ignored categories:")
    for category, count in ignored.get("category_counts", {}).items():
        print(f"    {category}: {count}")


if __name__ == "__main__":
    main()
