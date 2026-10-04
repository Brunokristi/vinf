from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import ExtractionPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract clean search documents from crawled BibleHub HTML."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Extract only the first N saved crawl pages.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project directory containing data/metadata/pages.jsonl.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    pipeline = ExtractionPipeline(args.project_root)
    summary = pipeline.run(limit=args.limit)
    print(json.dumps(summary, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
