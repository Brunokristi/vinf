from __future__ import annotations

import json
import os
from pathlib import Path
import unittest

from extractor.atlas import extract_atlas
from extractor.bible import extract_bible
from extractor.commentary import extract_commentary
from extractor.topical import extract_topical


PROJECT_ROOT = Path(os.environ.get("BSE_PROJECT_ROOT", Path.cwd())).resolve()
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"
MANIFEST = SAMPLES_DIR / "manifest.jsonl"


def load_records() -> list[dict]:
    if not MANIFEST.exists():
        raise unittest.SkipTest(f"Sample manifest not found: {MANIFEST}")
    return [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sample_path(record: dict) -> Path:
    group = record["crawl_group"]
    number = int(record["sample_number"])
    matches = sorted((SAMPLES_DIR / group).glob(f"{number:02d}_*.html"))
    if not matches:
        raise AssertionError(f"Missing sample for {group} #{number}")
    return matches[0]


def extract(record: dict) -> dict:
    html = sample_path(record).read_text(encoding="utf-8", errors="replace")
    group = record["crawl_group"]
    url = record["url"]
    if group == "bible":
        return extract_bible(html, url)
    if group == "commentary":
        return extract_commentary(html, url)
    if group in {"topical", "naves", "torrey"}:
        return extract_topical(html, url, crawl_group=group)
    if group == "atlas":
        return extract_atlas(html, url)
    raise AssertionError(f"Unsupported sample group: {group}")


class ExtractorSampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = load_records()

    def records_for(self, group: str) -> list[dict]:
        return [r for r in self.records if r["crawl_group"] == group]

    def test_bible_samples(self) -> None:
        expected_counts = {
            "https://biblehub.com/ezekiel/1.htm": 28,
            "https://biblehub.com/1_samuel/21.htm": 15,
            "https://biblehub.com/john/4.htm": 54,
            "https://biblehub.com/psalms/3.htm": 8,
            "https://biblehub.com/micah/1.htm": 16,
        }
        for record in self.records_for("bible"):
            with self.subTest(url=record["url"]):
                document = extract(record)
                self.assertEqual(document["verse_count"], expected_counts[record["url"]])
                self.assertTrue(document["text"])
                self.assertNotIn("Footnotes:", document["text"])
                self.assertNotIn("Berean Standard Bible", document["text"])

    def test_commentary_samples(self) -> None:
        for record in self.records_for("commentary"):
            with self.subTest(url=record["url"]):
                document = extract(record)
                self.assertGreater(len(document["text"]), 100)
                self.assertNotIn("\nLinks\n", document["text"])
                self.assertNotIn("Parallel Texts", document["text"])

    def test_topical_samples(self) -> None:
        forbidden = ("\nSubtopics\n", "\nRelated Terms\n", "\nLibrary\n", "\nStrong's Hebrew\n")
        for record in self.records_for("topical"):
            with self.subTest(url=record["url"]):
                document = extract(record)
                self.assertGreater(len(document["text"]), 100)
                for marker in forbidden:
                    self.assertNotIn(marker, document["text"])

    def test_naves_samples(self) -> None:
        for record in self.records_for("naves"):
            with self.subTest(url=record["url"]):
                document = extract(record)
                self.assertTrue(document["sections"]["article"])
                self.assertTrue(document["sections"]["naves_index"])
                self.assertNotIn("\nLibrary\n", document["text"])
                self.assertNotIn("\nRelated Terms\n", document["text"])

    def test_torrey_samples(self) -> None:
        for record in self.records_for("torrey"):
            with self.subTest(url=record["url"]):
                document = extract(record)
                self.assertTrue(document["sections"]["article"])
                self.assertTrue(document["sections"]["torrey_textbook"])
                self.assertNotIn("\nLibrary\n", document["text"])
                self.assertNotIn("\nRelated Terms\n", document["text"])

    def test_atlas_samples(self) -> None:
        for record in self.records_for("atlas"):
            with self.subTest(url=record["url"]):
                document = extract(record)
                self.assertTrue(document["sections"]["occurrences"])
                self.assertTrue(document["sections"]["encyclopedia"])
                self.assertNotIn("\nStrong's Hebrew\n", document["text"])
                self.assertNotIn("\nStrong's Greek\n", document["text"])


if __name__ == "__main__":
    unittest.main()
