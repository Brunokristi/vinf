from __future__ import annotations

import argparse
import json

from .config import Settings
from .crawler import BiblicalCrawler, with_delay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Focused BibleHub crawler for the Biblical Search Engine project.")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Maximum number of HTML pages to save in this run (default: 20).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Override delay between HTTP requests in seconds.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.max_pages <= 0:
        raise SystemExit("--max-pages must be greater than zero")

    settings = with_delay(Settings(), args.delay)

    if "replace-me@example.com" in settings.user_agent:
        print(
            "WARNING: Replace the placeholder contact in crawler/config.py or set "
            "BSE_USER_AGENT before a real crawl."
        )

    crawler = BiblicalCrawler(settings)
    summary = crawler.crawl(max_pages=args.max_pages)

    print("\nRun summary:")
    print(json.dumps(summary, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
