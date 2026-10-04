from crawler.url_utils import (
    audit_discovered_url,
    classify_url_details,
    derive_supported_urls,
)


def test_bible_book_directory_is_discovery_page():
    result = classify_url_details("https://biblehub.com/genesis/")
    assert result is not None
    assert result.crawl_group == "bible"
    assert result.document_type == "bible_index"
    assert result.is_discovery is True


def test_bible_verse_derives_commentary_url_and_is_audited():
    source = "https://biblehub.com/genesis/1.htm"
    verse = "/genesis/1-12.htm"

    assert derive_supported_urls(verse, source) == [
        "https://biblehub.com/commentaries/genesis/1-12.htm"
    ]

    audited = audit_discovered_url(verse, source)
    assert audited is not None
    assert audited.category == "bible_verse"
    assert audited.reason == "derived_resource"


def test_commentary_author_collection_has_clear_audit_category():
    audited = audit_discovered_url(
        "/commentaries/meyer/revelation/22.htm",
        "https://biblehub.com/commentaries/revelation/22-21.htm",
    )
    assert audited is not None
    assert audited.category == "commentary_collection"
    assert audited.reason == "unsupported_collection"


def test_atlas_collection_has_clear_audit_category():
    audited = audit_discovered_url(
        "/atlas/shepherd/",
        "https://biblehub.com/atlas/",
    )
    assert audited is not None
    assert audited.category == "atlas_collection"
    assert audited.reason == "unsupported_collection"
