from crawler.url_utils import classify_url, normalize_url


def test_normalize_relative_url_and_remove_fragment():
    result = normalize_url("../exodus/3.htm#top", "https://biblehub.com/genesis/1.htm")
    assert result == "https://biblehub.com/exodus/3.htm"


def test_normalize_removes_query_parameters():
    result = normalize_url("https://biblehub.com/genesis/1.htm?utm_source=test&view=mobile")
    assert result == "https://biblehub.com/genesis/1.htm"


def test_external_domain_is_rejected():
    assert normalize_url("https://example.com/page.htm") is None


def test_bible_page_classification():
    assert classify_url("https://biblehub.com/1_samuel/17.htm") == "bible"


def test_commentary_page_classification():
    assert classify_url("https://biblehub.com/commentaries/genesis/1-1.htm") == "commentary"


def test_topical_page_classification():
    assert classify_url("https://biblehub.com/topical/m/moses_and_the_exodus.htm") == "topical"


def test_atlas_page_classification():
    assert classify_url("https://biblehub.com/atlas/jerusalem.htm") == "atlas"


def test_irrelevant_biblehub_page_is_rejected():
    assert classify_url("https://biblehub.com/greek/3056.htm") is None
