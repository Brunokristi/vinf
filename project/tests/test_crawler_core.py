from __future__ import annotations

from crawler.link_extractor import extract_links
from crawler.url_utils import normalize_url


def test_normalize_url_removes_fragment() -> None:
    assert normalize_url(
        "/genesis/1.htm#verse1",
        "https://biblehub.com/",
    ) == "https://biblehub.com/genesis/1.htm"


def test_link_extractor_keeps_supported_internal_links() -> None:
    html = """
    <html><body>
        <a href="/genesis/1.htm">Genesis 1</a>
        <a href="/commentaries/john/3-16.htm">John commentary</a>
        <a href="https://example.com/outside">Outside</a>
    </body></html>
    """
    links, total = extract_links(html, "https://biblehub.com/")
    assert total == 3
    assert "https://biblehub.com/genesis/1.htm" in links
    assert "https://biblehub.com/commentaries/john/3-16.htm" in links
    assert all("example.com" not in link for link in links)
