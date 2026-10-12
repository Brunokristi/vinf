from __future__ import annotations

import json
from pathlib import Path

from extractor.pipeline import ExtractionPipeline


def test_extraction_pipeline_writes_valid_document(tmp_path: Path) -> None:
    raw_dir = tmp_path / "data" / "raw" / "html"
    metadata_dir = tmp_path / "data" / "metadata"
    raw_dir.mkdir(parents=True)
    metadata_dir.mkdir(parents=True)

    html = """
    <html><head><title>Genesis 1</title></head><body>
    <span class="reftext"><b>1</b></span>
    <div>In the beginning God created the heavens and the earth with purpose and order.</div>
    <span class="reftext"><b>2</b></span>
    <div>The earth was formless and empty while the narrative continues with sufficient text.</div>
    <div>Footnotes:</div><div>do not keep</div>
    </body></html>
    """
    raw_path = raw_dir / "abc.html"
    raw_path.write_text(html, encoding="utf-8")

    metadata = {
        "document_id": "abc",
        "url": "https://biblehub.com/genesis/1.htm",
        "document_type": "bible",
        "crawl_group": "bible",
        "fetch_status": "saved",
        "raw_html_path": "data/raw/html/abc.html",
        "content_hash": "sourcehash",
    }
    (metadata_dir / "pages.jsonl").write_text(
        json.dumps(metadata) + "\n",
        encoding="utf-8",
    )

    summary = ExtractionPipeline(tmp_path).run()
    assert summary["valid_documents"] == 1
    assert summary["invalid_documents"] == 0

    documents = (
        tmp_path / "data" / "processed" / "documents.jsonl"
    ).read_text(encoding="utf-8").splitlines()
    document = json.loads(documents[0])
    assert document["verse_count"] == 2
    assert "do not keep" not in document["text"]
