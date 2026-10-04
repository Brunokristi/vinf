from crawler.link_extractor import extract_links


def test_extracts_only_supported_biblehub_links():
    html = """
    <html>
        <body>
            <a href="/genesis/2.htm">Genesis 2</a>
            <a href="/commentaries/genesis/1-1.htm">Commentary</a>
            <a href="/atlas/jerusalem.htm">Jerusalem</a>
            <a href="https://example.com/elsewhere">External</a>
            <a href="/greek/3056.htm">Greek</a>
            <a href="/genesis/2.htm#top">Duplicate</a>
        </body>
    </html>
    """

    links, total = extract_links(html, "https://biblehub.com/genesis/1.htm")

    assert total == 6
    assert links == [
        "https://biblehub.com/genesis/2.htm",
        "https://biblehub.com/commentaries/genesis/1-1.htm",
        "https://biblehub.com/atlas/jerusalem.htm",
    ]
