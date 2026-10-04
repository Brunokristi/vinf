from crawler.url_utils import audit_discovered_url, classify_url_details


def test_supported_url_has_crawl_group():
    result = classify_url_details("https://biblehub.com/topical/m/moses.htm")
    assert result is not None
    assert result.crawl_group == "topical"
    assert result.document_type == "topical"
    assert result.is_discovery is False


def test_discovery_url_uses_same_crawl_group():
    result = classify_url_details("https://biblehub.com/topical/a.htm")
    assert result is not None
    assert result.crawl_group == "topical"
    assert result.document_type == "topical_index"
    assert result.is_discovery is True


def test_unsupported_internal_url_is_audited_by_category():
    result = audit_discovered_url(
        "/greek/3056.htm",
        "https://biblehub.com/genesis/1.htm",
    )
    assert result is not None
    assert result.category == "greek"
    assert result.reason == "unsupported_internal_section"


def test_external_url_is_audited():
    result = audit_discovered_url(
        "https://example.com/page?q=1",
        "https://biblehub.com/genesis/1.htm",
    )
    assert result is not None
    assert result.url == "https://example.com/page"
    assert result.reason == "external_domain"
    assert result.category == "example.com"
