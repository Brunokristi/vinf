from __future__ import annotations

import json
from pathlib import Path

from extractor.pipeline import ExtractionPipeline


BIBLE_HTML = """
<html>
<head><title>Genesis 1</title></head>
<body>
    <div>BSB</div>
    <a>1</a><span>In the beginning God created the heavens and the earth.</span>
    <a>2</a><span>Now the earth was formless and void, and darkness covered the deep.</span>
    <div>Footnotes:</div>
</body>
</html>
"""


def test_pipeline_creates_valid_documents_and_summary(tmp_path: Path):
    raw_dir = tmp_path / "data" / "raw" / "html"
    metadata_dir = tmp_path / "data" / "metadata"
    raw_dir.mkdir(parents=True)
    metadata_dir.mkdir(parents=True)

    raw_path = raw_dir / "abc.html"
    raw_path.write_text(BIBLE_HTML, encoding="utf-8")

    metadata = {
        "document_id": "abc",
        "url": "https://biblehub.com/genesis/1.htm",
        "document_type": "bible",
        "fetch_status": "saved",
        "fetched_at": "2026-10-04T10:00:00+00:00",
        "content_hash": "sourcehash",
        "raw_html_path": "data/raw/html/abc.html",
    }
    (metadata_dir / "pages.jsonl").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )

    summary = ExtractionPipeline(tmp_path).run()

    assert summary["source_pages"] == 1
    assert summary["valid_documents"] == 1
    assert summary["invalid_documents"] == 0
    assert summary["success_rate_percent"] == 100.0

    documents_path = tmp_path / "data" / "processed" / "documents.jsonl"
    document = json.loads(documents_path.read_text(encoding="utf-8"))
    assert document["document_type"] == "bible"
    assert document["valid"] is True
    assert document["verse_count"] == 2


def test_pipeline_skips_old_discovery_pages(tmp_path: Path):
    raw_dir = tmp_path / "data" / "raw" / "html"
    metadata_dir = tmp_path / "data" / "metadata"
    raw_dir.mkdir(parents=True)
    metadata_dir.mkdir(parents=True)

    root_html = "<html><head><title>Topical</title></head><body>Directory</body></html>"
    raw_path = raw_dir / "topical-root.html"
    raw_path.write_text(root_html, encoding="utf-8")

    # Simulate metadata created by extractor/crawler version 0.1, where the
    # topical root was still labelled as a topical document.
    metadata = {
        "document_id": "topical-root",
        "url": "https://biblehub.com/topical/",
        "document_type": "topical",
        "fetch_status": "saved",
        "raw_html_path": "data/raw/html/topical-root.html",
    }
    (metadata_dir / "pages.jsonl").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )

    summary = ExtractionPipeline(tmp_path).run()

    assert summary["source_pages"] == 1
    assert summary["eligible_documents"] == 0
    assert summary["valid_documents"] == 0
    assert summary["invalid_documents"] == 0
    assert summary["skipped_documents"] == 1
    assert summary["skipped_discovery_pages"] == 1
