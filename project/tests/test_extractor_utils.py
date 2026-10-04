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
