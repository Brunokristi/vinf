from crawler.link_extractor import extract_links_with_audit


def test_verse_link_derives_commentary_without_crawling_duplicate_verse_page():
    html = '''
    <html><body>
        <a href="/genesis/1-1.htm">Genesis 1:1</a>
        <a href="/genesis/2.htm">Genesis 2</a>
    </body></html>
    '''

    result = extract_links_with_audit(html, "https://biblehub.com/genesis/1.htm")

    assert "https://biblehub.com/genesis/1-1.htm" not in result.eligible
    assert "https://biblehub.com/commentaries/genesis/1-1.htm" in result.eligible
    assert result.derived == ["https://biblehub.com/commentaries/genesis/1-1.htm"]
    assert "https://biblehub.com/genesis/2.htm" in result.eligible
    assert any(item.category == "bible_verse" for item in result.ignored)
