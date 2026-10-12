from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

from .atlas import extract_atlas
from .bible import extract_bible
from .commentary import extract_commentary
from .topical import extract_topical
from .utils import crawl_group_from_url, is_discovery_page, text_hash, utc_now
from .validator import validate_document


@dataclass(frozen=True)
class ExtractionPaths:
    project_root: Path

    @property
    def pages_file(self) -> Path:
        return self.project_root / "data" / "metadata" / "pages.jsonl"

    @property
    def processed_dir(self) -> Path:
        return self.project_root / "data" / "processed"

    @property
    def documents_file(self) -> Path:
        return self.processed_dir / "documents.jsonl"

    @property
    def invalid_file(self) -> Path:
        return self.processed_dir / "invalid_documents.jsonl"

    @property
    def summary_file(self) -> Path:
        return self.processed_dir / "extraction_summary.json"


class ExtractionPipeline:
    def __init__(self, project_root: Path):
        self.paths = ExtractionPaths(project_root.resolve())
        self.paths.processed_dir.mkdir(parents=True, exist_ok=True)

    def _load_pages(self) -> list[dict]:
        if not self.paths.pages_file.exists():
            raise FileNotFoundError(f"Crawler metadata not found: {self.paths.pages_file}")

        pages: list[dict] = []
        with self.paths.pages_file.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    pages.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of {self.paths.pages_file}"
                    ) from exc
        return pages

    def _resolve_raw_path(self, metadata: dict) -> Path:
        raw_value = metadata.get("raw_html_path")
        if not raw_value:
            raise ValueError("metadata_missing_raw_html_path")
        raw_path = Path(raw_value)
        return raw_path if raw_path.is_absolute() else self.paths.project_root / raw_path

    @staticmethod
    def _write_jsonl(handle, record: dict) -> None:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _extract(html: str, metadata: dict) -> dict:
        url = str(metadata.get("url") or "")
        document_type = str(metadata.get("document_type") or "")
        crawl_group = str(
            metadata.get("crawl_group")
            or crawl_group_from_url(url, document_type)
            or document_type
        )

        if crawl_group == "bible":
            return extract_bible(html, url)
        if crawl_group == "commentary":
            return extract_commentary(html, url)
        if crawl_group in {"topical", "naves", "torrey"}:
            return extract_topical(html, url, crawl_group=crawl_group)
        if crawl_group == "atlas":
            return extract_atlas(html, url)
        raise ValueError(f"unsupported_crawl_group:{crawl_group}")

    def run(self, limit: int | None = None) -> dict:
        pages = [p for p in self._load_pages() if p.get("fetch_status") == "saved"]
        if limit is not None:
            pages = pages[:limit]

        started_at = utc_now()
        type_counts: Counter[str] = Counter()
        group_counts: Counter[str] = Counter()
        valid_type_counts: Counter[str] = Counter()
        valid_group_counts: Counter[str] = Counter()
        source_collection_counts: Counter[str] = Counter()
        error_counts: Counter[str] = Counter()
        valid_count = invalid_count = skipped_count = skipped_discovery_pages = 0
        skipped_non_content_pages = 0
        skip_reason_counts: Counter[str] = Counter()
        total_text_characters = 0

        with (
            self.paths.documents_file.open("w", encoding="utf-8") as documents_handle,
            self.paths.invalid_file.open("w", encoding="utf-8") as invalid_handle,
        ):
            for metadata in pages:
                document_type = str(metadata.get("document_type") or "")
                url = str(metadata.get("url") or "")
                crawl_group = str(
                    metadata.get("crawl_group")
                    or crawl_group_from_url(url, document_type)
                    or document_type
                )

                if metadata.get("is_discovery_page") or is_discovery_page(url):
                    skipped_count += 1
                    skipped_discovery_pages += 1
                    continue

                if crawl_group not in {"bible", "commentary", "topical", "naves", "torrey", "atlas"}:
                    skipped_count += 1
                    continue

                type_counts[document_type] += 1
                group_counts[crawl_group] += 1

                try:
                    raw_path = self._resolve_raw_path(metadata)
                    html = raw_path.read_text(encoding="utf-8", errors="replace")
                    extracted = self._extract(html, metadata)
                    skip_reason = extracted.pop("_skip_reason", None)
                    if skip_reason:
                        skipped_count += 1
                        skipped_non_content_pages += 1
                        skip_reason_counts[str(skip_reason)] += 1
                        continue

                    document = {
                        "document_id": metadata["document_id"],
                        "url": url,
                        "document_type": document_type,
                        "crawl_group": crawl_group,
                        "fetched_at": metadata.get("fetched_at"),
                        "extracted_at": utc_now(),
                        "extractor_version": "1.2-regex-config",
                        "raw_html_path": metadata.get("raw_html_path"),
                        "source_content_hash": metadata.get("content_hash"),
                        **extracted,
                    }

                    document["text_length"] = len(document.get("text") or "")
                    document["word_count"] = len((document.get("text") or "").split())
                    document["text_hash"] = text_hash(document.get("text") or "")
                    validation_errors = validate_document(document)
                    document["valid"] = not validation_errors
                    document["validation_errors"] = validation_errors

                    if validation_errors:
                        invalid_count += 1
                        error_counts.update(validation_errors)
                        self._write_jsonl(invalid_handle, document)
                    else:
                        valid_count += 1
                        valid_type_counts[document_type] += 1
                        valid_group_counts[crawl_group] += 1
                        collection = document.get("source_collection")
                        if collection:
                            source_collection_counts[str(collection)] += 1
                        total_text_characters += document["text_length"]
                        self._write_jsonl(documents_handle, document)

                except Exception as exc:
                    invalid_count += 1
                    error_counts[type(exc).__name__] += 1
                    self._write_jsonl(invalid_handle, {
                        "document_id": metadata.get("document_id"),
                        "url": url,
                        "document_type": document_type,
                        "crawl_group": crawl_group,
                        "valid": False,
                        "validation_errors": [f"extractor_error:{type(exc).__name__}"],
                        "error": str(exc),
                    })

        eligible = valid_count + invalid_count
        summary = {
            "started_at": started_at,
            "finished_at": utc_now(),
            "source_pages": len(pages),
            "eligible_documents": eligible,
            "valid_documents": valid_count,
            "invalid_documents": invalid_count,
            "skipped_documents": skipped_count,
            "skipped_discovery_pages": skipped_discovery_pages,
            "skipped_non_content_pages": skipped_non_content_pages,
            "skip_reason_counts": dict(sorted(skip_reason_counts.items())),
            "success_rate_percent": round(valid_count / eligible * 100, 2) if eligible else 0.0,
            "total_text_characters": total_text_characters,
            "source_type_counts": dict(sorted(type_counts.items())),
            "source_group_counts": dict(sorted(group_counts.items())),
            "valid_type_counts": dict(sorted(valid_type_counts.items())),
            "valid_group_counts": dict(sorted(valid_group_counts.items())),
            "valid_source_collection_counts": dict(sorted(source_collection_counts.items())),
            "validation_error_counts": dict(sorted(error_counts.items())),
            "documents_file": str(self.paths.documents_file.relative_to(self.paths.project_root)),
            "invalid_file": str(self.paths.invalid_file.relative_to(self.paths.project_root)),
        }

        self.paths.summary_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return summary
