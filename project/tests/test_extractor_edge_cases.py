from __future__ import annotations

import unittest

from extractor.commentary import extract_commentary
from extractor.topical import extract_topical
from extractor.validator import validate_document


class ExtractorEdgeCaseTests(unittest.TestCase):
    def test_dictionary_topical_fallback(self):
        html = """
        <html><head><title>Topical Bible: stingy</title></head><body>
        <div>Webster's Revised Unabridged Dictionary</div>
        <div>1. (a.) Meanly covetous or petty; stingy; closefisted.</div>
        <div>2. (adv.) In a miser manner.</div>
        <div>Strong's Hebrew</div><div>3596. kilay -- a rascal</div>
        </body></html>
        """
        result = extract_topical(html, "https://biblehub.com/topical/n/niggardly.htm")
        self.assertIn("Meanly covetous", result["sections"]["dictionary"])
        self.assertNotIn("Strong's Hebrew", result["text"])
        self.assertIsNone(result["_skip_reason"])

    def test_navigation_only_topical_is_marked_for_skip(self):
        html = """
        <html><head><title>Topical Bible: The Godly</title></head><body>
        <div>Topical Encyclopedia</div>
        <div>Subtopics</div>
        <div>Godly</div>
        <div>Related Terms</div>
        </body></html>
        """
        result = extract_topical(html, "https://biblehub.com/topical/t/the_godly.htm")
        self.assertEqual(result["text"], "")
        self.assertEqual(result["_skip_reason"], "navigation_only_topical_page")

    def test_collapsed_commentary_markers_are_split_by_config(self):
        html = (
            "<html><head><title>1 John 1:8 Commentaries</title></head><body>"
            "intro EXPOSITORY (ENGLISH BIBLE)<a>Benson Commentary</a> useful commentary "
            "Links<a>1 John 1:8 Interlinear</a></body></html>"
        )
        result = extract_commentary(
            html,
            "https://biblehub.com/commentaries/1_john/1-8.htm",
        )
        self.assertIn("useful commentary", result["text"])
        self.assertNotIn("Interlinear", result["text"])


if __name__ == "__main__":
    unittest.main()
