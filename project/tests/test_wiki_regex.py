from spark.wiki_regex import parse_page


def test_parse_wikipedia_page() -> None:
    xml = """
    <page>
        <title>Jerusalem</title>
        <ns>0</ns>
        <id>12345</id>
        <revision>
            <id>99999</id>
            <text xml:space="preserve">
            '''Jerusalem''' is an ancient city.

            [[David]] ruled from Jerusalem.
            See also [[Temple Mount|the Temple Mount]].

            [[Category:Ancient cities]]
            [[Category:Biblical places]]
            </text>
        </revision>
    </page>
    """

    page = parse_page(xml)

    assert page is not None
    assert page["page_id"] == 12345
    assert page["title"] == "Jerusalem"
    assert page["namespace"] == 0
    assert page["join_key"] == "jerusalem"

    assert "Ancient cities" in page["categories"]
    assert "Biblical places" in page["categories"]

    assert "David" in page["internal_links"]
    assert "Temple Mount" in page["internal_links"]

    assert "Jerusalem" in page["preview"]