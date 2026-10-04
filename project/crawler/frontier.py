from __future__ import annotations

from collections import deque
from pathlib import Path

from .storage import Storage
from .url_utils import normalize_url


class Frontier:
    def __init__(self, storage: Storage, seed_file: Path):
        self.storage = storage
        self.visited = set(storage.load_lines(storage.visited_file))

        seen_order = storage.load_lines(storage.seen_file)
        self.seen = set(seen_order)
        self.queue = deque(url for url in seen_order if url not in self.visited)

        if not seen_order:
            self._load_seeds(seed_file)

    def _load_seeds(self, seed_file: Path) -> None:
        if not seed_file.exists():
            raise FileNotFoundError(f"Seed file does not exist: {seed_file}")

        for raw_url in seed_file.read_text(encoding="utf-8").splitlines():
            raw_url = raw_url.strip()
            if not raw_url or raw_url.startswith("#"):
                continue
            self.add(raw_url)

    def add(self, url: str) -> bool:
        normalized = normalize_url(url)
        if normalized is None or normalized in self.seen:
            return False

        self.seen.add(normalized)
        self.queue.append(normalized)
        self.storage.append_line(self.storage.seen_file, normalized)
        return True

    def pop(self) -> str | None:
        while self.queue:
            url = self.queue.popleft()
            if url not in self.visited:
                return url
        return None

    def mark_visited(self, url: str) -> None:
        if url in self.visited:
            return

        self.visited.add(url)
        self.storage.append_line(self.storage.visited_file, url)

    def __len__(self) -> int:
        return len(self.queue)
