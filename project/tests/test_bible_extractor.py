from extractor.bible import extract_bible


HTML = """
<html>
<head><title>Genesis 1: The Creation</title></head>
<body>
    <div>Bible</div>
    <div>Genesis 1</div>
    <div>BSB</div>
    <h2>The Creation</h2>
    <a>1</a><span>In the beginning God created the heavens and the earth.</span>
    <a>2</a><span>Now the earth was formless and void, and darkness was over the deep.</span>
    <h3>The First Day</h3>
    <a>3</a><span>And God said, Let there be light, and there was light.</span>
    <div>Footnotes:</div>
    <div>3 a Some footnote that must not be part of the text.</div>
    <div>Genesis 1 Summary</div>
</body>
</html>
"""


def test_bible_extractor_reads_book_chapter_and_verses():
    result = extract_bible(HTML, "https://biblehub.com/genesis/1.htm")

    assert result["book"] == "Genesis"
    assert result["chapter"] == 1
    assert result["verse_count"] == 3
    assert result["verses"][0]["verse"] == 1
    assert "In the beginning" in result["verses"][0]["text"]
    assert "Footnotes" not in result["text"]
    assert "Genesis 1 Summary" not in result["text"]
