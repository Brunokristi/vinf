from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import shutil


GROUPS = (
    "bible",
    "commentary",
    "topical",
    "naves",
    "torrey",
    "atlas",
)


def load_pages(metadata_path: Path, project_root: Path) -> dict[str, list[dict]]:
    pages_by_group = {
        group: []
        for group in GROUPS
    }

    with metadata_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()

            if not line:
                continue

            metadata = json.loads(line)

            if metadata.get("fetch_status") != "saved":
                continue

            if metadata.get("is_discovery_page"):
                continue

            crawl_group = metadata.get("crawl_group")

            if crawl_group not in pages_by_group:
                continue

            raw_html_path = metadata.get("raw_html_path")

            if not raw_html_path:
                continue

            raw_path = Path(raw_html_path)

            if not raw_path.is_absolute():
                raw_path = project_root / raw_path

            if not raw_path.exists():
                continue

            metadata["_resolved_raw_path"] = raw_path

            pages_by_group[crawl_group].append(metadata)

    return pages_by_group


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select sample raw HTML pages for extractor analysis."
    )

    parser.add_argument(
        "--per-group",
        type=int,
        default=5,
        help="Number of pages to select from each crawl group.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed so the same sample can be reproduced.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/samples"),
        help="Directory where sampled HTML files will be copied.",
    )

    args = parser.parse_args()

    project_root = Path.cwd().resolve()

    metadata_path = (
        project_root
        / "data"
        / "metadata"
        / "pages.jsonl"
    )

    if not metadata_path.exists():
        raise SystemExit(
            f"Metadata file not found: {metadata_path}"
        )

    random_generator = random.Random(args.seed)

    pages_by_group = load_pages(
        metadata_path=metadata_path,
        project_root=project_root,
    )

    output_dir = args.output

    if not output_dir.is_absolute():
        output_dir = project_root / output_dir

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest_path = output_dir / "manifest.jsonl"

    with manifest_path.open("w", encoding="utf-8") as manifest:
        for group in GROUPS:
            pages = pages_by_group[group]

            print()
            print("=" * 80)
            print(group.upper())
            print("=" * 80)
            print(f"Available pages: {len(pages)}")

            if not pages:
                print("No pages available.")
                continue

            sample_size = min(
                args.per_group,
                len(pages),
            )

            selected = random_generator.sample(
                pages,
                sample_size,
            )

            group_dir = output_dir / group

            group_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            for index, metadata in enumerate(selected, start=1):
                source_path = metadata["_resolved_raw_path"]

                destination_path = (
                    group_dir
                    / f"{index:02d}_{source_path.name}"
                )

                shutil.copy2(
                    source_path,
                    destination_path,
                )

                record = {
                    "sample_number": index,
                    "crawl_group": group,
                    "document_type": metadata.get("document_type"),
                    "url": metadata.get("url"),
                    "title": metadata.get("title"),
                    "source_raw_html_path": str(source_path),
                    "sample_html_path": str(destination_path),
                }

                manifest.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                print()
                print(f"{index}. {metadata.get('url')}")
                print(f"   title: {metadata.get('title')}")
                print(f"   file:  {destination_path}")

    print()
    print("=" * 80)
    print(f"Samples saved to: {output_dir}")
    print(f"Manifest:         {manifest_path}")


if __name__ == "__main__":
    main()