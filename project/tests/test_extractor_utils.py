from extractor.utils import (
    parse_bible_url,
    parse_commentary_url,
    place_from_url,
    topic_from_url,
)


def test_parse_bible_url():
    assert parse_bible_url("https://biblehub.com/1_samuel/17.htm") == ("1 Samuel", 17)


def test_parse_commentary_verse_url():
    assert parse_commentary_url(
        "https://biblehub.com/commentaries/genesis/1-1.htm"
    ) == ("Genesis", 1, 1)


def test_parse_commentary_chapter_url():
    assert parse_commentary_url(
        "https://biblehub.com/commentaries/genesis/1.htm"
    ) == ("Genesis", 1, None)


def test_topic_from_url():
    assert topic_from_url(
        "https://biblehub.com/topical/m/moses_and_the_exodus.htm"
    ) == "Moses And The Exodus"


def test_place_from_url():
    assert place_from_url("https://biblehub.com/atlas/jerusalem.htm") == "Jerusalem"


def test_discovery_pages_are_detected():
    from extractor.utils import is_discovery_page

    assert is_discovery_page("https://biblehub.com/topical/") is True
    assert is_discovery_page("https://biblehub.com/topical/a.htm") is True
    assert is_discovery_page("https://biblehub.com/atlas/") is True
    assert is_discovery_page("https://biblehub.com/atlas/b.htm") is True
    assert is_discovery_page("https://biblehub.com/topical/m/moses.htm") is False
    assert is_discovery_page("https://biblehub.com/atlas/jerusalem.htm") is False


def test_zero_width_boundaries_are_normalized_to_spaces():
    from extractor.utils import normalize_line

    assert normalize_line("Let there be\u200ban expanse") == "Let there be an expanse"
    assert normalize_line("He wore a\u200bbronze coat") == "He wore a bronze coat"
    assert normalize_line("tree\u200bof life") == "tree of life"
    assert normalize_line("In Him\u200bwas life") == "In Him was life"
    assert normalize_line("a\u200bwitness") == "a witness"


def test_soft_hyphen_is_removed_without_splitting_word():
    from extractor.utils import normalize_line

    assert normalize_line("crea\u00adtion") == "creation"


def test_only_standalone_link_letters_are_removed_as_markers():
    from extractor.utils import html_to_lines

    html = """
    <html><body>
        <p>This is a real article a in normal text.</p>
        <p>There was light,<a href=\"#footnotes\">a</a> and it was good.</p>
    </body></html>
    """

    lines = html_to_lines(html)
    joined = " ".join(lines)
    assert "article a in normal text" in joined
    assert "light, a and" not in joined
    assert "light, and it was good" in joined
