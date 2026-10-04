from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from .config import Settings


class Storage:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pages_file = settings.metadata_dir / "pages.jsonl"
        self.errors_file = settings.errors_dir / "errors.jsonl"
        self.seen_file = settings.state_dir / "seen_urls.txt"
        self.visited_file = settings.state_dir / "visited_urls.txt"
        self.robots_file = settings.metadata_dir / "robots.txt"
        self.summary_file = settings.metadata_dir / "run_summary.json"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        self.settings.raw_html_dir.mkdir(parents=True, exist_ok=True)
        self.settings.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.settings.state_dir.mkdir(parents=True, exist_ok=True)
        self.settings.errors_dir.mkdir(parents=True, exist_ok=True)

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

    def save_robots(self, text: str) -> None:
        self.robots_file.write_text(text, encoding="utf-8")

    def save_summary(self, summary: dict) -> None:
        self.summary_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )

    def utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
