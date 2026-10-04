from crawler.link_extractor import extract_links_with_audit


def test_extract_links_returns_supported_and_ignored_links():
    html = """
    <html><body>
        <a href="/genesis/2.htm">Genesis 2</a>
        <a href="/topical/a.htm">Topical A</a>
        <a href="/greek/3056.htm">Greek</a>
        <a href="/greek/3056.htm?x=1">Greek duplicate</a>
        <a href="https://example.com/foo">External</a>
    </body></html>
    """

    result = extract_links_with_audit(html, "https://biblehub.com/genesis/1.htm")

    assert result.total_links == 5
    assert result.eligible == [
        "https://biblehub.com/genesis/2.htm",
        "https://biblehub.com/topical/a.htm",
    ]
    assert [(item.category, item.reason) for item in result.ignored] == [
        ("greek", "unsupported_internal_section"),
        ("example.com", "external_domain"),
    ]
