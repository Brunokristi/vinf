from extractor.topical import extract_topical


def test_naves_topical_title_and_collection():
    html = """<html><head><title>Topical Bible: Aaron: Character of</title></head>
    <body><div>Topical Encyclopedia</div><p>Aaron was a leader and priest.</p><div>Bible Hub</div></body></html>"""
    d = extract_topical(html, "https://biblehub.com/topical/naves/a/aaron--character_of.htm")
    assert d["title"] == "Aaron: Character of"
    assert d["topic"] == "Aaron: Character of"
    assert d["source_collection"] == "naves"
    assert "Aaron was a leader" in d["text"]


def test_torrey_topical_collection():
    html = """<html><head><title>Topical Bible: The Holy Spirit: is God</title></head>
    <body><div>Topical Encyclopedia</div><p>The Holy Spirit is described in Scripture.</p><div>Bible Hub</div></body></html>"""
    d = extract_topical(html, "https://biblehub.com/topical/ttt/t/the_holy_spirit--is_god.htm")
    assert d["source_collection"] == "torrey"
    assert d["title"] == "The Holy Spirit: is God"
