from __future__ import annotations

from collections import deque
from pathlib import Path

from .storage import Storage
from .url_groups import CRAWL_GROUP_NAMES
from .url_utils import crawl_group_for_url, normalize_url


class Frontier:
    """Persistent, balanced URL frontier with one FIFO queue per crawl group."""

    def __init__(self, storage: Storage, seed_file: Path):
        self.storage = storage
        self.visited = set(storage.load_lines(storage.visited_file))
        self.queues = {group: deque() for group in CRAWL_GROUP_NAMES}
        self.group_order = list(CRAWL_GROUP_NAMES)
        self._next_group_index = 0

        seen_order = storage.load_lines(storage.seen_file)
        self.seen = set(seen_order)

        for url in seen_order:
            if url in self.visited:
                continue
            self._enqueue_existing(url)

        # Always read seeds. Existing URLs are ignored by add(), while newly
        # configured groups/seeds can be introduced without deleting crawl state.
        self._load_seeds(seed_file)

    def _enqueue_existing(self, url: str) -> bool:
        group = crawl_group_for_url(url)
        if group is None or group not in self.queues:
            return False
        self.queues[group].append(url)
        return True

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

        group = crawl_group_for_url(normalized)
        if group is None or group not in self.queues:
            return False

        self.seen.add(normalized)
        self.queues[group].append(normalized)
        self.storage.append_line(self.storage.seen_file, normalized)
        return True

    def pop(self) -> tuple[str, str] | None:
        if not self.group_order:
            return None

        groups_checked = 0
        group_count = len(self.group_order)

        while groups_checked < group_count:
            group = self.group_order[self._next_group_index]
            self._next_group_index = (self._next_group_index + 1) % group_count
            groups_checked += 1

            queue = self.queues[group]
            while queue:
                url = queue.popleft()
                if url not in self.visited:
                    return url, group

        return None

    def mark_visited(self, url: str) -> None:
        if url in self.visited:
            return

        self.visited.add(url)
        self.storage.append_line(self.storage.visited_file, url)

    def counts(self) -> dict[str, int]:
        return {group: len(queue) for group, queue in self.queues.items()}

    def __len__(self) -> int:
        return sum(len(queue) for queue in self.queues.values())
