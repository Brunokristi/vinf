from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from .config import Settings
from .url_utils import AuditedUrl


class Storage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pages_file = settings.metadata_dir / "pages.jsonl"
        self.errors_file = settings.errors_dir / "errors.jsonl"
        self.seen_file = settings.state_dir / "seen_urls.txt"
        self.visited_file = settings.state_dir / "visited_urls.txt"
        self.ignored_urls_file = settings.state_dir / "ignored_urls.txt"
        self.ignored_details_file = settings.metadata_dir / "ignored_urls.jsonl"
        self.ignored_summary_file = settings.metadata_dir / "ignored_url_summary.json"
        self.robots_file = settings.metadata_dir / "robots.txt"
        self.summary_file = settings.metadata_dir / "run_summary.json"
        self._ensure_directories()
        self._ignored_urls = set(self.load_lines(self.ignored_urls_file))
        self._ignored_category_counts: Counter[str] = Counter()
        self._ignored_reason_counts: Counter[str] = Counter()
        self._load_ignored_counts()

    def _ensure_directories(self) -> None:
        self.settings.raw_html_dir.mkdir(parents=True, exist_ok=True)
        self.settings.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.settings.state_dir.mkdir(parents=True, exist_ok=True)
        self.settings.errors_dir.mkdir(parents=True, exist_ok=True)

    def _load_ignored_counts(self) -> None:
        if not self.ignored_details_file.exists():
            return

        with self.ignored_details_file.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                self._ignored_category_counts[str(record.get("category", "unknown"))] += 1
                self._ignored_reason_counts[str(record.get("reason", "unknown"))] += 1

    @staticmethod
    def load_lines(path: Path) -> list[str]:
        if not path.exists():
            return []

        return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @staticmethod
    def append_line(path: Path, value: str) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(value + "\n")

    @staticmethod
    def append_jsonl(path: Path, record: dict) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    def save_html(self, document_id: str, content: bytes) -> Path:
        path = self.settings.raw_html_dir / f"{document_id}.html"
        path.write_bytes(content)
        return path

    def save_page_metadata(self, record: dict) -> None:
        self.append_jsonl(self.pages_file, record)

    def save_error(self, record: dict) -> None:
        self.append_jsonl(self.errors_file, record)

    def record_ignored_url(self, audited: AuditedUrl, source_url: str) -> bool:
        if audited.url in self._ignored_urls:
            return False

        self._ignored_urls.add(audited.url)
        self.append_line(self.ignored_urls_file, audited.url)
        self.append_jsonl(self.ignored_details_file, {
            "url": audited.url,
            "reason": audited.reason,
            "category": audited.category,
            "source_url": source_url,
            "discovered_at": self.utc_now(),
        })
        self._ignored_category_counts[audited.category] += 1
        self._ignored_reason_counts[audited.reason] += 1
        return True

    def ignored_summary(self) -> dict:
        return {
            "ignored_urls_total": len(self._ignored_urls),
            "category_counts": dict(sorted(self._ignored_category_counts.items())),
            "reason_counts": dict(sorted(self._ignored_reason_counts.items())),
            "ignored_urls_file": str(self.ignored_urls_file.relative_to(self.settings.data_dir.parent)),
            "ignored_details_file": str(self.ignored_details_file.relative_to(self.settings.data_dir.parent)),
        }

    def save_ignored_summary(self) -> None:
        self.ignored_summary_file.write_text(
            json.dumps(self.ignored_summary(), ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def save_robots(self, text: str) -> None:
        self.robots_file.write_text(text, encoding="utf-8")

    def save_summary(self, summary: dict) -> None:
        self.summary_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
