from __future__ import annotations

import argparse
import json
from pathlib import Path

from .builder import InvertedIndexBuilder


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the custom inverted index.")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Index only the first N valid documents (useful for tests).",
    )
    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be greater than zero")

    stats = InvertedIndexBuilder(Path.cwd()).build(limit=args.limit)
    print(json.dumps(stats, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
