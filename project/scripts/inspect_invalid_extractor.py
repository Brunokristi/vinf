from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from extractor.regex_html import html_to_lines
from extractor.configs.topical import CONFIG as TOPICAL_CONFIG
from extractor.configs.commentary import CONFIG as COMMENTARY_CONFIG
from extractor.configs.atlas import CONFIG as ATLAS_CONFIG


CONFIG_BY_GROUP = {
    "topical": TOPICAL_CONFIG,
    "commentary": COMMENTARY_CONFIG,
    "atlas": ATLAS_CONFIG,
}

SECTION_HEADINGS = (
    re.compile(r"^Topical Encyclopedia(?: Introduction)?:?$", re.IGNORECASE),
    re.compile(r"^Nave's Topical Index$", re.IGNORECASE),
    re.compile(r"^Torrey's Topical Textbook$", re.IGNORECASE),
    re.compile(r"^EXPOSITORY \(ENGLISH BIBLE\)$", re.IGNORECASE),
    re.compile(r"^Occurrences$", re.IGNORECASE),
    re.compile(r"^Encyclopedia$", re.IGNORECASE),
    re.compile(r"^Resources$", re.IGNORECASE),
    re.compile(r"^Library$", re.IGNORECASE),
    re.compile(r"^Subtopics$", re.IGNORECASE),
    re.compile(r"^Related Terms$", re.IGNORECASE),
    re.compile(r"^Links$", re.IGNORECASE),
    re.compile(r"^Strong's (?:Greek|Hebrew)$", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)


def is_heading(line: str) -> bool:
    return any(pattern.search(line) for pattern in SECTION_HEADINGS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--invalid-file",
        type=Path,
        default=Path("data/processed/invalid_documents.jsonl"),
    )
    parser.add_argument("--context", type=int, default=3)
    args = parser.parse_args()

    documents = [
        json.loads(line)
        for line in args.invalid_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    for document in documents:
        group = document.get("crawl_group")
        if group not in CONFIG_BY_GROUP:
            continue

        raw_path = Path(document["raw_html_path"])
        html = raw_path.read_text(encoding="utf-8", errors="replace")
        lines = html_to_lines(html, CONFIG_BY_GROUP[group])

        print("=" * 100)
        print(group.upper(), document.get("url"))
        print("existing errors:", document.get("validation_errors"))

        heading_indexes = [i for i, line in enumerate(lines) if is_heading(line)]
        if not heading_indexes:
            print("No known section headings found.")
            print("First 30 cleaned lines:")
            for i, line in enumerate(lines[:30]):
                print(f"  {i:04d}: {line[:220]}")
            print()
            continue

        for index in heading_indexes:
            print(f"\n--- heading around cleaned line {index} ---")
            start = max(0, index - args.context)
            end = min(len(lines), index + args.context + 1)
            for current in range(start, end):
                prefix = ">>" if current == index else "  "
                print(f"{prefix} {current:04d}: {lines[current][:220]}")
        print()


if __name__ == "__main__":
    main()
