from __future__ import annotations

import pytest

from extractor.atlas import extract_atlas
from extractor.bible import extract_bible
from extractor.commentary import extract_commentary
from extractor.topical import extract_topical
from extractor.validator import validate_document


BIBLE_CASES = [
    ("https://biblehub.com/genesis/1.htm", "Genesis creation light heavens earth"),
    ("https://biblehub.com/exodus/3.htm", "Moses burning bush Egypt deliverance"),
    ("https://biblehub.com/psalms/23.htm", "Lord shepherd valley goodness mercy"),
    ("https://biblehub.com/john/3.htm", "Jesus Nicodemus eternal life world"),
    ("https://biblehub.com/romans/8.htm", "Spirit life hope creation glory"),
]

COMMENTARY_CASES = [
    ("https://biblehub.com/commentaries/genesis/1-1.htm", "creation"),
    ("https://biblehub.com/commentaries/exodus/3-14.htm", "Moses"),
    ("https://biblehub.com/commentaries/psalms/23-1.htm", "shepherd"),
    ("https://biblehub.com/commentaries/john/3-16.htm", "love"),
    ("https://biblehub.com/commentaries/romans/8-28.htm", "good"),
]

TOPICAL_CASES = [
    ("https://biblehub.com/topical/f/faith.htm", "Faith"),
    ("https://biblehub.com/topical/g/grace.htm", "Grace"),
    ("https://biblehub.com/topical/p/prayer.htm", "Prayer"),
    ("https://biblehub.com/topical/s/salvation.htm", "Salvation"),
    ("https://biblehub.com/topical/c/covenant.htm", "Covenant"),
]

NAVES_CASES = [
    ("https://biblehub.com/topical/naves/m/moses.htm", "Moses"),
    ("https://biblehub.com/topical/naves/a/abraham.htm", "Abraham"),
    ("https://biblehub.com/topical/naves/d/david.htm", "David"),
    ("https://biblehub.com/topical/naves/j/joseph.htm", "Joseph"),
    ("https://biblehub.com/topical/naves/p/prayer.htm", "Prayer"),
]

TORREY_CASES = [
    ("https://biblehub.com/topical/ttt/f/faith.htm", "Faith"),
    ("https://biblehub.com/topical/ttt/g/grace.htm", "Grace"),
    ("https://biblehub.com/topical/ttt/p/prayer.htm", "Prayer"),
    ("https://biblehub.com/topical/ttt/s/sin.htm", "Sin"),
    ("https://biblehub.com/topical/ttt/w/wisdom.htm", "Wisdom"),
]

ATLAS_CASES = [
    ("https://biblehub.com/atlas/jerusalem.htm", "Jerusalem"),
    ("https://biblehub.com/atlas/bethlehem.htm", "Bethlehem"),
    ("https://biblehub.com/atlas/nazareth.htm", "Nazareth"),
    ("https://biblehub.com/atlas/egypt.htm", "Egypt"),
    ("https://biblehub.com/atlas/jordan.htm", "Jordan"),
]


def bible_html(keyword: str) -> str:
    return f"""
    <html><head><title>Bible chapter</title></head><body>
    <span class="reftext"><b>1</b></span>
    <div>The first verse discusses {keyword} and contains enough meaningful text for validation.</div>
    <span class="reftext"><b>2</b></span>
    <div>The second verse continues the biblical narrative with additional context and detail.</div>
    <span class="reftext"><b>3</b></span>
    <div>The third verse completes this representative chapter extraction example.</div>
    <div>Footnotes:</div>
    <div>THIS FOOTNOTE MUST NOT BE EXTRACTED</div>
    </body></html>
    """


def commentary_html(keyword: str) -> str:
    return f"""
    <html><head><title>Commentary page</title></head><body>
    <div>EXPOSITORY (ENGLISH BIBLE)</div>
    <div>Benson Commentary</div>
    <p>This commentary explains {keyword} in its biblical context. It contains a sufficiently long
    discussion of the passage, its interpretation, historical setting, theological meaning, and
    relationship to the surrounding verses so the extractor has realistic content to preserve.</p>
    <div>Links</div>
    <div>INTERLINEAR NAVIGATION MUST NOT BE EXTRACTED</div>
    </body></html>
    """


def topical_html(topic: str) -> str:
    return f"""
    <html><head><title>Topical Bible: {topic}</title></head><body>
    <div>Topical Encyclopedia</div>
    <p>{topic} is discussed throughout Scripture and this representative article explains its
    biblical meaning, context, major references, and significance for readers.</p>
    <div>Subtopics</div>
    <div>UNRELATED NAVIGATION MUST NOT BE EXTRACTED</div>
    </body></html>
    """


def naves_html(topic: str) -> str:
    return f"""
    <html><head><title>Topical Bible: {topic}</title></head><body>
    <div>Topical Encyclopedia</div>
    <p>{topic} has a broad biblical background described in this article with enough context to
    form a meaningful searchable document for the project.</p>
    <div>Nave's Topical Index</div>
    <p>{topic}: representative Nave references include several passages and related biblical ideas
    that belong to the historical topical index section of this page.</p>
    <div>Resources</div>
    <div>RESOURCE NAVIGATION MUST NOT BE EXTRACTED</div>
    </body></html>
    """


def torrey_html(topic: str) -> str:
    return f"""
    <html><head><title>Topical Bible: {topic}</title></head><body>
    <div>Topical Encyclopedia</div>
    <p>{topic} is introduced with a substantial biblical explanation and enough descriptive text
    for a valid searchable article in the extracted corpus.</p>
    <div>Torrey's Topical Textbook</div>
    <p>{topic}: Torrey lists representative themes, related passages, doctrinal connections, and
    references that are retained as useful topical content.</p>
    <div>Library</div>
    <div>LIBRARY NAVIGATION MUST NOT BE EXTRACTED</div>
    </body></html>
    """


def atlas_html(place: str) -> str:
    return f"""
    <html><head><title>{place} Atlas</title></head><body>
    <div>Occurrences</div>
    <p>{place} appears in multiple biblical passages and these occurrence notes retain useful
    geographic context for search and retrieval.</p>
    <div>Encyclopedia</div>
    <p>{place} is an important biblical location with historical, geographic, and narrative
    information preserved by the atlas extractor.</p>
    <div>Strong's Hebrew</div>
    <div>LEXICAL NAVIGATION MUST NOT BE EXTRACTED</div>
    </body></html>
    """


def assert_valid(document: dict, *, url: str, document_type: str, crawl_group: str) -> None:
    validation_document = {
        "url": url,
        "document_type": document_type,
        "crawl_group": crawl_group,
        **document,
    }
    assert validate_document(validation_document) == []


@pytest.mark.parametrize("url,keyword", BIBLE_CASES, ids=[url for url, _ in BIBLE_CASES])
def test_bible_pages(url: str, keyword: str) -> None:
    document = extract_bible(bible_html(keyword), url)
    assert document["verse_count"] == 3
    assert keyword in document["text"]
    assert "THIS FOOTNOTE" not in document["text"]
    assert_valid(document, url=url, document_type="bible", crawl_group="bible")


@pytest.mark.parametrize("url,keyword", COMMENTARY_CASES, ids=[url for url, _ in COMMENTARY_CASES])
def test_commentary_pages(url: str, keyword: str) -> None:
    document = extract_commentary(commentary_html(keyword), url)
    assert keyword in document["text"]
    assert "INTERLINEAR NAVIGATION" not in document["text"]
    assert document["sections"]["commentary"]
    assert_valid(document, url=url, document_type="commentary", crawl_group="commentary")


@pytest.mark.parametrize("url,topic", TOPICAL_CASES, ids=[url for url, _ in TOPICAL_CASES])
def test_contemporary_topical_pages(url: str, topic: str) -> None:
    document = extract_topical(topical_html(topic), url, crawl_group="topical")
    assert topic in document["text"]
    assert "UNRELATED NAVIGATION" not in document["text"]
    assert document["source_collection"] == "contemporary"
    assert_valid(document, url=url, document_type="topical", crawl_group="topical")


@pytest.mark.parametrize("url,topic", NAVES_CASES, ids=[url for url, _ in NAVES_CASES])
def test_naves_pages(url: str, topic: str) -> None:
    document = extract_topical(naves_html(topic), url, crawl_group="naves")
    assert document["sections"]["article"]
    assert document["sections"]["naves_index"]
    assert "RESOURCE NAVIGATION" not in document["text"]
    assert document["source_collection"] == "naves"
    assert_valid(document, url=url, document_type="topical", crawl_group="naves")


@pytest.mark.parametrize("url,topic", TORREY_CASES, ids=[url for url, _ in TORREY_CASES])
def test_torrey_pages(url: str, topic: str) -> None:
    document = extract_topical(torrey_html(topic), url, crawl_group="torrey")
    assert document["sections"]["article"]
    assert document["sections"]["torrey_textbook"]
    assert "LIBRARY NAVIGATION" not in document["text"]
    assert document["source_collection"] == "torrey"
    assert_valid(document, url=url, document_type="topical", crawl_group="torrey")


@pytest.mark.parametrize("url,place", ATLAS_CASES, ids=[url for url, _ in ATLAS_CASES])
def test_atlas_pages(url: str, place: str) -> None:
    document = extract_atlas(atlas_html(place), url)
    assert document["has_occurrences"] is True
    assert document["has_encyclopedia"] is True
    assert place in document["text"]
    assert "LEXICAL NAVIGATION" not in document["text"]
    assert_valid(document, url=url, document_type="atlas", crawl_group="atlas")


def test_dictionary_fallback_and_navigation_stub() -> None:
    dictionary_html = """
    <html><head><title>Topical Bible: Stingy</title></head><body>
    <div>Webster's Revised Unabridged Dictionary</div>
    <div>Meanly covetous or petty; stingy; closefisted.</div>
    <div>Strong's Hebrew</div><div>navigation noise</div>
    </body></html>
    """
    dictionary = extract_topical(
        dictionary_html,
        "https://biblehub.com/topical/s/stingy.htm",
        crawl_group="topical",
    )
    assert "Meanly covetous" in dictionary["text"]
    assert "navigation noise" not in dictionary["text"]

    navigation_html = """
    <html><head><title>Topical Bible: The Godly</title></head><body>
    <div>Topical Encyclopedia</div><div>Subtopics</div><div>Godly</div>
    </body></html>
    """
    navigation = extract_topical(
        navigation_html,
        "https://biblehub.com/topical/t/the_godly.htm",
        crawl_group="topical",
    )
    assert navigation["_skip_reason"] == "navigation_only_topical_page"
