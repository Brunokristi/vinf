from __future__ import annotations

import json
from pathlib import Path

import pytest

from extractor.atlas import extract_atlas
from extractor.bible import extract_bible
from extractor.commentary import extract_commentary
from extractor.topical import extract_topical
from extractor.validator import validate_document


SAMPLES_DIR = Path("data/samples")
MANIFEST = SAMPLES_DIR / "manifest.jsonl"


def test_real_sample_corpus_when_available() -> None:
    """Regression-check at least 20 real sampled crawler pages when present.

    The code ZIP intentionally does not contain the crawled dataset. On the
    project server, where data/samples exists, this test verifies the actual
    sampled BibleHub HTML pages. The self-contained fixture suite covers the
    same six groups when the dataset is not available.
    """
    if not MANIFEST.exists():
        pytest.skip("data/samples/manifest.jsonl is not included in the code archive")

    records = [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(records) >= 20, "The REGEX bonus requires at least 20 sampled pages"

    checked = 0
    for record in records:
        group = record["crawl_group"]
        url = record["url"]
        number = int(record["sample_number"])
        matches = sorted((SAMPLES_DIR / group).glob(f"{number:02d}_*.html"))
        assert matches, f"Missing sampled HTML for {group} #{number}: {url}"

        html = matches[0].read_text(encoding="utf-8", errors="replace")

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
            raise AssertionError(f"Unsupported sample group: {group}")

        assert not extracted.get("_skip_reason"), f"Unexpected skip for {url}"
        document = {
            "url": url,
            "document_type": document_type,
            "crawl_group": group,
            **extracted,
        }
        assert validate_document(document) == [], f"Invalid extraction for {url}"
        checked += 1

    assert checked >= 20
