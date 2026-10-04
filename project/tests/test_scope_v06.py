from crawler.url_utils import classify_url_details, audit_discovered_url


def test_naves_is_its_own_balanced_group_but_topical_document():
    c = classify_url_details("https://biblehub.com/topical/naves/a/aaron--character_of.htm")
    assert c is not None
    assert c.crawl_group == "naves"
    assert c.document_type == "topical"
    assert c.is_discovery is False


def test_torrey_is_its_own_balanced_group_but_topical_document():
    c = classify_url_details("https://biblehub.com/topical/ttt/t/the_holy_spirit--is_god--as_jehovah.htm")
    assert c is not None
    assert c.crawl_group == "torrey"
    assert c.document_type == "topical"
    assert c.is_discovery is False


def test_naves_and_torrey_landing_pages_are_discovery():
    n = classify_url_details("https://biblehub.com/topical/naves.htm")
    t = classify_url_details("https://biblehub.com/topical/ttt.htm")
    assert n is not None and n.crawl_group == "naves" and n.is_discovery
    assert t is not None and t.crawl_group == "torrey" and t.is_discovery


def test_atlas_full_is_audited_as_duplicate_representation():
    a = audit_discovered_url(
        "https://biblehub.com/atlas/full/abana_river.htm",
        "https://biblehub.com/atlas/abana_river.htm",
    )
    assert a is not None
    assert a.category == "atlas_full_duplicate"
    assert a.reason == "duplicate_representation"


def test_commentary_collection_directory_is_classified_cleanly():
    a = audit_discovered_url(
        "https://biblehub.com/commentaries/benson/genesis/",
        "https://biblehub.com/commentaries/",
    )
    assert a is not None
    assert a.category == "commentary_collection_index"
