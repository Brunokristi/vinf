from __future__ import annotations

import argparse
import json
from pathlib import Path

from .atlas import extract_atlas
from .bible import extract_bible
from .commentary import extract_commentary
from .topical import extract_topical
from .utils import crawl_group_from_url
from .validator import validate_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check regex extraction on sampled raw pages.")
    parser.add_argument("--samples-dir", type=Path, default=Path("data/samples"))
    parser.add_argument("--preview-chars", type=int, default=800)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    samples_dir = args.samples_dir.resolve()
    manifest = samples_dir / "manifest.jsonl"
    if not manifest.exists():
        raise SystemExit(f"Sample manifest not found: {manifest}")

    total = valid = 0
    with manifest.open("r", encoding="utf-8") as handle:
        for raw in handle:
            record = json.loads(raw)
            group = record["crawl_group"]
            url = record["url"]
            # Prefer the local samples-dir copy even when the manifest was
            # created on a different machine/path.
            candidates = sorted((samples_dir / group).glob(f"{int(record['sample_number']):02d}_*.html"))
            if not candidates:
                print(f"MISSING {group} {url}")
                continue
            html = candidates[0].read_text(encoding="utf-8", errors="replace")

            if group == "bible":
                extracted = extract_bible(html, url)
                document_type = "bible"
            elif group == "commentary":
                extracted = extract_commentary(html, url)
                document_type = "commentary"
            elif group in {"topical", "naves", "torrey"}:
                extracted = extract_topical(html, url, crawl_group=group)
                document_type = "topical"
            elif group == "atlas":
                extracted = extract_atlas(html, url)
                document_type = "atlas"
            else:
                continue

            document = {"url": url, "document_type": document_type, "crawl_group": group, **extracted}
            errors = validate_document(document)
            total += 1
            if not errors:
                valid += 1

            print("=" * 100)
            print(f"{group.upper()} | {url}")
            print(f"title: {extracted.get('title')}")
            print(f"valid: {not errors} errors={errors}")
            if group == "bible":
                print(f"verses: {extracted.get('verse_count')}")
            print("sections:", ", ".join(extracted.get("sections", {}).keys()) or "-")
            text = str(extracted.get("text") or "")
            print(f"chars: {len(text)}")
            print(text[:args.preview_chars].replace("\n", " "))
            print()

    print("=" * 100)
    print(f"VALID: {valid}/{total}")


if __name__ == "__main__":
    main()
