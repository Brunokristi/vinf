from __future__ import annotations

from collections import Counter
from dataclasses import replace
import hashlib
import time

from bs4 import BeautifulSoup
import requests

from .config import Settings
from .downloader import Downloader
from .frontier import Frontier
from .link_extractor import extract_links_with_audit
from .robots import RobotsPolicy
from .storage import Storage
from .url_utils import classify_url_details, normalize_url


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
        ignored_discovered = 0
        derived_discovered = 0
        saved_by_group: Counter[str] = Counter()
        saved_by_document_type: Counter[str] = Counter()

        while downloaded < max_pages:
            next_item = self.frontier.pop()
            if next_item is None:
                break

            url, scheduled_group = next_item
            classification = classify_url_details(url)
            if classification is None:
                self.frontier.mark_visited(url)
                continue

            if not self.robots.can_fetch(url):
                robots_blocked += 1
                self.frontier.mark_visited(url)
                self.storage.save_page_metadata({
                    "document_id": self.document_id(url),
                    "url": url,
                    "crawl_group": classification.crawl_group,
                    "document_type": classification.document_type,
                    "is_discovery_page": classification.is_discovery,
                    "fetch_status": "robots_blocked",
                    "fetched_at": self.storage.utc_now(),
                })
                print(f"[ROBOTS] group={scheduled_group} {url}")
                continue

            print(f"[GET] group={scheduled_group} {url}")
            result = self.downloader.fetch(url)
            requests_attempted += result.attempts
            self.frontier.mark_visited(url)

            if result.response is None:
                failed += 1
                self.storage.save_error({
                    "kind": "request_error",
                    "url": url,
                    "crawl_group": classification.crawl_group,
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
                "crawl_group": classification.crawl_group,
                "document_type": classification.document_type,
                "is_discovery_page": classification.is_discovery,
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

            final_classification = (
                classify_url_details(final_url)
                if final_url is not None
                else None
            )
            if final_classification is None:
                failed += 1
                self.storage.save_page_metadata({
                    **base_metadata,
                    "fetch_status": "redirected_outside_scope",
                })
                print(f"[SKIP redirect] {url} -> {response.url}")
                continue

            html = response.text
            links = extract_links_with_audit(html, final_url)
            new_links = 0
            new_derived = 0
            derived_set = set(links.derived)

            for link in links.eligible:
                if self.frontier.add(link):
                    new_links += 1
                    if link in derived_set:
                        new_derived += 1

            new_ignored = 0
            for audited in links.ignored:
                if self.storage.record_ignored_url(audited, final_url):
                    new_ignored += 1

            discovered += new_links
            ignored_discovered += new_ignored
            derived_discovered += new_derived
            raw_path = self.storage.save_html(self.document_id(url), response.content)

            self.storage.save_page_metadata({
                **base_metadata,
                "fetch_status": "saved",
                "title": self.extract_title(html),
                "content_hash": self.content_hash(response.content),
                "raw_html_path": str(raw_path.relative_to(self.settings.data_dir.parent)),
                "links_total": links.total_links,
                "links_eligible": len(links.eligible),
                "links_new": new_links,
                "links_derived": len(links.derived),
                "derived_new": new_derived,
                "links_ignored": len(links.ignored),
                "ignored_new": new_ignored,
            })

            downloaded += 1
            saved_by_group[classification.crawl_group] += 1
            saved_by_document_type[classification.document_type] += 1
            print(
                f"[SAVED {downloaded}/{max_pages}] "
                f"group={classification.crawl_group} "
                f"type={classification.document_type} "
                f"links_new={new_links} derived_new={new_derived} "
                f"ignored_new={new_ignored} {url}"
            )

        self.storage.save_ignored_summary()
        summary = {
            "started_at": started_at,
            "finished_at": self.storage.utc_now(),
            "duration_seconds": round(time.monotonic() - started_monotonic, 3),
            "pages_saved": downloaded,
            "saved_by_group": dict(sorted(saved_by_group.items())),
            "saved_by_document_type": dict(sorted(saved_by_document_type.items())),
            "requests_attempted": requests_attempted,
            "robots_blocked": robots_blocked,
            "failed": failed,
            "non_html": non_html,
            "new_urls_discovered": discovered,
            "new_ignored_urls_discovered": ignored_discovered,
            "new_derived_urls_discovered": derived_discovered,
            "ignored_urls": self.storage.ignored_summary(),
            "frontier_remaining": len(self.frontier),
            "frontier_by_group": self.frontier.counts(),
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
