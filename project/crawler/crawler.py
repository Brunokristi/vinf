from __future__ import annotations

from dataclasses import replace
import hashlib
from pathlib import Path
import time

from bs4 import BeautifulSoup
import requests

from .config import Settings
from .downloader import Downloader
from .frontier import Frontier
from .link_extractor import extract_links
from .robots import RobotsPolicy
from .storage import Storage
from .url_utils import classify_url, normalize_url


class BiblicalCrawler:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.storage = Storage(settings)
        self.session = requests.Session()
        self.session.headers.update(settings.headers)
        self.downloader = Downloader(settings, self.session)
        self.frontier = Frontier(self.storage, settings.seed_file)
        self.robots = RobotsPolicy(settings, self.storage, self.session)

    @staticmethod
    def document_id(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]

    @staticmethod
    def content_hash(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def extract_title(html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        if soup.title is None:
            return None
        title = soup.title.get_text(" ", strip=True)
        return title or None

    def crawl(self, max_pages: int = 20) -> dict:
        started_at = self.storage.utc_now()
        started_monotonic = time.monotonic()

        self.robots.load()

        downloaded = 0
        requests_attempted = 0
        robots_blocked = 0
        failed = 0
        non_html = 0
        discovered = 0

        while downloaded < max_pages:
            url = self.frontier.pop()
            if url is None:
                break

            document_type = classify_url(url)
            if document_type is None:
                self.frontier.mark_visited(url)
                continue

            if not self.robots.can_fetch(url):
                robots_blocked += 1
                self.frontier.mark_visited(url)
                self.storage.save_page_metadata({
                    "document_id": self.document_id(url),
                    "url": url,
                    "document_type": document_type,
                    "fetch_status": "robots_blocked",
                    "fetched_at": self.storage.utc_now(),
                })
                print(f"[ROBOTS] {url}")
                continue

            print(f"[GET] {url}")
            result = self.downloader.fetch(url)
            requests_attempted += result.attempts
            self.frontier.mark_visited(url)

            if result.response is None:
                failed += 1
                self.storage.save_error({
                    "kind": "request_error",
                    "url": url,
                    "error": result.error,
                    "attempts": result.attempts,
                    "fetched_at": self.storage.utc_now(),
                })
                print(f"[ERROR] {url}: {result.error}")
                continue

            response = result.response
            final_url = normalize_url(response.url)
            status_code = response.status_code
            content_type = response.headers.get("Content-Type", "")

            base_metadata = {
                "document_id": self.document_id(url),
                "url": url,
                "final_url": final_url,
                "document_type": document_type,
                "fetched_at": self.storage.utc_now(),
                "status_code": status_code,
                "content_type": content_type,
                "content_length": len(response.content),
                "attempts": result.attempts,
            }

            if status_code != 200:
                failed += 1
                self.storage.save_page_metadata({
                    **base_metadata,
                    "fetch_status": "http_error",
                })
                print(f"[HTTP {status_code}] {url}")
                continue

            if "text/html" not in content_type.lower():
                non_html += 1
                self.storage.save_page_metadata({
                    **base_metadata,
                    "fetch_status": "skipped_non_html",
                })
                print(f"[SKIP non-HTML] {url}")
                continue

            if final_url is None or classify_url(final_url) is None:
                failed += 1
                self.storage.save_page_metadata({
                    **base_metadata,
                    "fetch_status": "redirected_outside_scope",
                })
                print(f"[SKIP redirect] {url} -> {response.url}")
                continue

            html = response.text
            eligible_links, total_links = extract_links(html, final_url)
            new_links = 0

            for link in eligible_links:
                if self.frontier.add(link):
                    new_links += 1

            discovered += new_links
            raw_path = self.storage.save_html(self.document_id(url), response.content)

            self.storage.save_page_metadata({
                **base_metadata,
                "fetch_status": "saved",
                "title": self.extract_title(html),
                "content_hash": self.content_hash(response.content),
                "raw_html_path": str(raw_path.relative_to(self.settings.data_dir.parent)),
                "links_total": total_links,
                "links_eligible": len(eligible_links),
                "links_new": new_links,
            })

            downloaded += 1
            print(
                f"[SAVED {downloaded}/{max_pages}] "
                f"type={document_type} links_new={new_links} {url}"
            )

        summary = {
            "started_at": started_at,
            "finished_at": self.storage.utc_now(),
            "duration_seconds": round(time.monotonic() - started_monotonic, 3),
            "pages_saved": downloaded,
            "requests_attempted": requests_attempted,
            "robots_blocked": robots_blocked,
            "failed": failed,
            "non_html": non_html,
            "new_urls_discovered": discovered,
            "frontier_remaining": len(self.frontier),
            "seen_total": len(self.frontier.seen),
            "visited_total": len(self.frontier.visited),
        }
        self.storage.save_summary(summary)
        return summary


def with_delay(settings: Settings, delay: float | None) -> Settings:
    if delay is None:
        return settings
    if delay < 0:
        raise ValueError("Delay must be zero or greater")
    return replace(settings, download_delay=delay)
