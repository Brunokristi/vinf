from __future__ import annotations

from urllib.robotparser import RobotFileParser

import requests

from .config import Settings
from .storage import Storage


class RobotsPolicy:
    def __init__(self, settings: Settings, storage: Storage, session: requests.Session):
        self.settings = settings
        self.storage = storage
        self.session = session
        self.parser = RobotFileParser()
        self.loaded = False
        self.allow_all = False
        self.deny_all = False

    def load(self) -> None:
        robots_url = self.settings.base_url.rstrip("/") + "/robots.txt"

        try:
            response = self.session.get(
                robots_url,
                timeout=(self.settings.connect_timeout, self.settings.read_timeout),
                allow_redirects=True,
            )
        except requests.RequestException as exc:
            if self.settings.robots_fail_closed:
                self.deny_all = True
            else:
                self.allow_all = True
            self.loaded = True
            self.storage.save_error({
                "kind": "robots_fetch_error",
                "url": robots_url,
                "error": str(exc),
                "fetched_at": self.storage.utc_now(),
            })
            return

        if response.status_code == 404:
            self.allow_all = True
            self.loaded = True
            self.storage.save_robots("# robots.txt returned HTTP 404; no rules loaded.\n")
            return

        if response.status_code != 200:
            if self.settings.robots_fail_closed:
                self.deny_all = True
            else:
                self.allow_all = True
            self.loaded = True
            self.storage.save_error({
                "kind": "robots_http_error",
                "url": robots_url,
                "status_code": response.status_code,
                "fetched_at": self.storage.utc_now(),
            })
            return

        self.storage.save_robots(response.text)
        self.parser.set_url(robots_url)
        self.parser.parse(response.text.splitlines())
        self.loaded = True

    def can_fetch(self, url: str) -> bool:
        if not self.loaded:
            raise RuntimeError("robots.txt policy must be loaded before crawling")

        if self.allow_all:
            return True

        if self.deny_all:
            return False

        return self.parser.can_fetch(self.settings.user_agent, url)
