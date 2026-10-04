from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://biblehub.com/"
    allowed_domain: str = "biblehub.com"
    user_agent: str = os.getenv(
        "BSE_USER_AGENT",
        "BiblicalSearchEngine/0.1 (student research project; contact: replace-me@example.com)",
    )
    accept: str = "text/html,application/xhtml+xml"
    accept_language: str = "en-US,en;q=0.9"
    download_delay: float = 3.0
    connect_timeout: float = 10.0
    read_timeout: float = 20.0
    retry_times: int = 2
    max_retry_after: int = 120
    robots_fail_closed: bool = True
    seed_file: Path = PROJECT_ROOT / "config" / "seed_urls.txt"
    data_dir: Path = PROJECT_ROOT / "data"

    @property
    def raw_html_dir(self) -> Path:
        return self.data_dir / "raw" / "html"

    @property
    def metadata_dir(self) -> Path:
        return self.data_dir / "metadata"

    @property
    def state_dir(self) -> Path:
        return self.data_dir / "state"

    @property
    def errors_dir(self) -> Path:
        return self.data_dir / "errors"

    @property
    def headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": self.accept,
            "Accept-Language": self.accept_language,
            "Connection": "keep-alive",
        }
