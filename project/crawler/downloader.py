from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import time

import requests

from .config import Settings


@dataclass
class FetchResult:
    response: requests.Response | None
    error: str | None
    attempts: int


class Downloader:
    def __init__(self, settings: Settings, session: requests.Session):
        self.settings = settings
        self.session = session
        self.last_request_at: float | None = None

    def _respect_delay(self) -> None:
        if self.last_request_at is None:
            return

        elapsed = time.monotonic() - self.last_request_at
        remaining = self.settings.download_delay - elapsed
        if remaining > 0:
            time.sleep(remaining)

    def _retry_after_seconds(self, response: requests.Response, attempt: int) -> float:
        header = response.headers.get("Retry-After")

        if header:
            try:
                return min(float(header), float(self.settings.max_retry_after))
            except ValueError:
                try:
                    retry_at = parsedate_to_datetime(header)
                    if retry_at.tzinfo is None:
                        retry_at = retry_at.replace(tzinfo=timezone.utc)
                    seconds = (retry_at - datetime.now(timezone.utc)).total_seconds()
                    return min(max(seconds, 0.0), float(self.settings.max_retry_after))
                except (TypeError, ValueError, OverflowError):
                    pass

        return min(self.settings.download_delay * (2 ** attempt), float(self.settings.max_retry_after))

    def fetch(self, url: str) -> FetchResult:
        max_attempts = self.settings.retry_times + 1
        last_error: str | None = None

        for attempt in range(max_attempts):
            self._respect_delay()

            try:
                self.last_request_at = time.monotonic()
                response = self.session.get(
                    url,
                    timeout=(self.settings.connect_timeout, self.settings.read_timeout),
                    allow_redirects=True,
                )
            except requests.RequestException as exc:
                last_error = str(exc)
                if attempt + 1 < max_attempts:
                    time.sleep(self.settings.download_delay * (2 ** attempt))
                    continue
                return FetchResult(None, last_error, attempt + 1)

            if response.status_code in {429, 503} and attempt + 1 < max_attempts:
                time.sleep(self._retry_after_seconds(response, attempt))
                continue

            if 500 <= response.status_code < 600 and attempt + 1 < max_attempts:
                time.sleep(self.settings.download_delay * (2 ** attempt))
                continue

            return FetchResult(response, None, attempt + 1)

        return FetchResult(None, last_error or "Unknown fetch failure", max_attempts)
