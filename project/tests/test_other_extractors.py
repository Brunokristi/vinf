from extractor.atlas import extract_atlas
from extractor.commentary import extract_commentary
from extractor.topical import extract_topical


COMMENTARY_HTML = """
<html>
<head><title>Genesis 1:1 Commentaries</title></head>
<body>
    <div>Bible &gt; Commentaries &gt; Genesis 1:1</div>
    <div>Genesis 1:1</div>
    <div>In the beginning God created the heaven and the earth.</div>
    <div>Jump to:</div>
    <div>Barnes</div><div>Benson</div><div>Ellicott</div>
    <h2>EXPOSITORY (ENGLISH BIBLE)</h2>
    <h3>Ellicott's Commentary for English Readers</h3>
    <p>This commentary explains the opening words of Genesis in substantial detail.</p>
    <h3>Benson Commentary</h3>
    <p>This is another substantial commentary paragraph for the same verse.</p>
    <div>Parallel Commentaries</div>
    <div>Navigation that must not be extracted.</div>
</body>
</html>
"""

TOPICAL_HTML = """
<html>
<head><title>Topical Bible: Moses</title></head>
<body>
    <div>Bible &gt; Topical &gt; Moses</div>
    <div>Jump to: Hitchcock's • Smith's • ATS</div>
    <h2>Topical Encyclopedia Introduction:</h2>
    <p>Moses is one of the most significant figures in the Bible, serving as a prophet and leader.</p>
    <h3>Early Life:</h3>
    <p>Moses was born to Hebrew parents and was raised in Egypt.</p>
    <h3>The Exodus:</h3>
    <p>Moses led the Israelites out of Egypt after confronting Pharaoh.</p>
    <div>Bible Hub</div>
    <div>Footer navigation</div>
</body>
</html>
"""

ATLAS_HTML = """
<html>
<head><title>Bible Map: Jerusalem</title></head>
<body>
    <div>Bible &gt; Atlas &gt; Jerusalem</div>
    <div>Atlas</div>
    <h2>Jerusalem and surrounding area</h2>
    <h3>Occurrences</h3>
    <p>Joshua 10:1 mentions Jerusalem in a narrative context.</p>
    <p>1 Samuel 17:54 also mentions Jerusalem.</p>
    <h3>Encyclopedia</h3>
    <p>JERUSALEM is an important city with extensive historical material.</p>
    <div>Bible Hub</div>
    <div>Footer navigation</div>
</body>
</html>
"""


def test_commentary_extractor_removes_jump_list_and_footer():
    result = extract_commentary(
        COMMENTARY_HTML,
        "https://biblehub.com/commentaries/genesis/1-1.htm",
    )

    assert result["reference"] == "Genesis 1:1"
    assert "Ellicott's Commentary" in result["text"]
    assert "Benson Commentary" in result["text"]
    assert "Jump to" not in result["text"]
    assert "Navigation that must not be extracted" not in result["text"]


def test_topical_extractor_starts_at_introduction():
    result = extract_topical(
        TOPICAL_HTML,
        "https://biblehub.com/topical/m/moses.htm",
    )

    assert result["topic"] == "Moses"
    assert "Moses is one of the most significant figures" in result["text"]
    assert "The Exodus:" in result["text"]
    assert "Jump to" not in result["text"]
    assert "Footer navigation" not in result["text"]


def test_atlas_extractor_keeps_occurrences_and_encyclopedia():
    result = extract_atlas(
        ATLAS_HTML,
        "https://biblehub.com/atlas/jerusalem.htm",
    )

    assert result["place"] == "Jerusalem"
    assert result["has_occurrences"] is True
    assert result["has_encyclopedia"] is True
    assert "Occurrences" in result["text"]
    assert "Encyclopedia" in result["text"]
    assert "Footer navigation" not in result["text"]
