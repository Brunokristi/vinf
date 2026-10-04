from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Pattern


BOOK_SLUGS = {
    "genesis",
    "exodus",
    "leviticus",
    "numbers",
    "deuteronomy",
    "joshua",
    "judges",
    "ruth",
    "1_samuel",
    "2_samuel",
    "1_kings",
    "2_kings",
    "1_chronicles",
    "2_chronicles",
    "ezra",
    "nehemiah",
    "esther",
    "job",
    "psalms",
    "proverbs",
    "ecclesiastes",
    "songs",
    "isaiah",
    "jeremiah",
    "lamentations",
    "ezekiel",
    "daniel",
    "hosea",
    "joel",
    "amos",
    "obadiah",
    "jonah",
    "micah",
    "nahum",
    "habakkuk",
    "zephaniah",
    "haggai",
    "zechariah",
    "malachi",
    "matthew",
    "mark",
    "luke",
    "john",
    "acts",
    "romans",
    "1_corinthians",
    "2_corinthians",
    "galatians",
    "ephesians",
    "philippians",
    "colossians",
    "1_thessalonians",
    "2_thessalonians",
    "1_timothy",
    "2_timothy",
    "titus",
    "philemon",
    "hebrews",
    "james",
    "1_peter",
    "2_peter",
    "1_john",
    "2_john",
    "3_john",
    "jude",
    "revelation",
}

BOOK_RE = "|".join(sorted((re.escape(book) for book in BOOK_SLUGS), key=len, reverse=True))
BIBLE_VERSE_RE = re.compile(rf"^/(?P<book>{BOOK_RE})/(?P<chapter>\d+)-(?P<verse>\d+)\.htm$")


@dataclass(frozen=True)
class UrlGroupSpec:
    """Declarative definition of one crawl group.

    ``name`` controls scheduling/frontier balancing. ``document_type`` controls
    which extractor/index document type is produced. They may differ, which lets
    several source collections share one logical document type without changing
    the scheduler.
    """

    name: str
    document_type: str
    content_patterns: tuple[Pattern[str], ...]
    discovery_patterns: tuple[Pattern[str], ...] = ()

    def matches_content(self, path: str) -> bool:
        return any(pattern.fullmatch(path) for pattern in self.content_patterns)

    def matches_discovery(self, path: str) -> bool:
        return any(pattern.fullmatch(path) for pattern in self.discovery_patterns)


URL_GROUPS: tuple[UrlGroupSpec, ...] = (
    UrlGroupSpec(
        name="bible",
        document_type="bible",
        content_patterns=(re.compile(rf"^/(?:{BOOK_RE})/\d+\.htm$"),),
        discovery_patterns=(
            re.compile(rf"^/(?:{BOOK_RE})/$"),
            re.compile(rf"^/(?:{BOOK_RE})/index\.htm$"),
        ),
    ),
    UrlGroupSpec(
        name="commentary",
        document_type="commentary",
        content_patterns=(
            re.compile(rf"^/commentaries/(?:{BOOK_RE})/\d+(?:-\d+)?\.htm$"),
        ),
        discovery_patterns=(
            re.compile(r"^/commentaries/$"),
            re.compile(r"^/commentaries/index\.html?$"),
        ),
    ),
    UrlGroupSpec(
        name="naves",
        document_type="topical",
        content_patterns=(
            re.compile(r"^/topical/naves/[^/]+/[^/]+\.htm$"),
        ),
        discovery_patterns=(
            re.compile(r"^/topical/naves\.htm$"),
        ),
    ),
    UrlGroupSpec(
        name="torrey",
        document_type="topical",
        content_patterns=(
            re.compile(r"^/topical/ttt/[^/]+/[^/]+\.htm$"),
        ),
        discovery_patterns=(
            re.compile(r"^/topical/ttt\.htm$"),
        ),
    ),
    UrlGroupSpec(
        name="topical",
        document_type="topical",
        content_patterns=(re.compile(r"^/topical/[^/]+/[^/]+\.htm$"),),
        discovery_patterns=(
            re.compile(r"^/topical/$"),
            re.compile(r"^/topical/index\.html?$"),
            re.compile(r"^/topical/[a-z]\.htm$"),
        ),
    ),
    UrlGroupSpec(
        name="atlas",
        document_type="atlas",
        content_patterns=(re.compile(r"^/atlas/[^/]+\.htm$"),),
        discovery_patterns=(
            re.compile(r"^/atlas/$"),
            re.compile(r"^/atlas/index\.html?$"),
            re.compile(r"^/atlas/[a-z]\.htm$"),
        ),
    ),
)


CRAWL_GROUP_NAMES: tuple[str, ...] = tuple(group.name for group in URL_GROUPS)


# Audit categories for links deliberately outside the active crawl scope.
# Specific patterns must come before broad fallbacks.
IGNORED_INTERNAL_PATTERNS: tuple[tuple[str, str, Pattern[str]], ...] = (
    ("bible_verse", "derived_resource", BIBLE_VERSE_RE),
    (
        "commentary_collection",
        "unsupported_collection",
        re.compile(rf"^/commentaries/[^/]+/(?:{BOOK_RE})/\d+(?:-\d+)?\.htm$"),
    ),
    (
        "commentary_collection_index",
        "unsupported_collection",
        re.compile(rf"^/commentaries/[^/]+/(?:{BOOK_RE})/$"),
    ),
    ("commentary_other", "unsupported_internal_url", re.compile(r"^/commentaries(?:/|$)")),
    ("atlas_collection", "unsupported_collection", re.compile(r"^/atlas/[^/.]+/$")),
    ("atlas_full_duplicate", "duplicate_representation", re.compile(r"^/atlas/full/[^/]+\.htm$")),
    ("atlas_biblemapper", "unsupported_collection", re.compile(r"^/atlas/biblemapper(?:/|$)")),
    ("atlas_other", "unsupported_internal_url", re.compile(r"^/atlas(?:/|$)")),
    ("topical_other", "unsupported_internal_url", re.compile(r"^/topical(?:/|$)")),
    ("greek", "unsupported_internal_section", re.compile(r"^/greek(?:/|$)")),
    ("hebrew", "unsupported_internal_section", re.compile(r"^/hebrew(?:/|$)")),
    ("interlinear", "unsupported_internal_section", re.compile(r"^/interlinear(?:/|$)")),
    ("parallel", "unsupported_internal_section", re.compile(r"^/parallel(?:/|$)")),
    ("sermons", "unsupported_internal_section", re.compile(r"^/sermons(?:/|$)")),
    ("questions", "unsupported_internal_section", re.compile(r"^/(?:questions|q)(?:/|$)")),
    ("library", "unsupported_internal_section", re.compile(r"^/library(?:/|$)")),
    ("concordance", "unsupported_internal_section", re.compile(r"^/concordance(?:/|$)")),
    ("dictionary", "unsupported_internal_section", re.compile(r"^/(?:dictionary|dictionaries)(?:/|$)")),
    ("search", "unsupported_internal_section", re.compile(r"^/search")),
    ("translation_bsb", "unsupported_translation", re.compile(r"^/bsb(?:/|$)")),
    ("translation_niv", "unsupported_translation", re.compile(r"^/niv(?:/|$)")),
    ("translation_kjv", "unsupported_translation", re.compile(r"^/kjv(?:/|$)")),
    ("translation_esv", "unsupported_translation", re.compile(r"^/esv(?:/|$)")),
    ("translation_nlt", "unsupported_translation", re.compile(r"^/nlt(?:/|$)")),
    ("translation_nasb", "unsupported_translation", re.compile(r"^/nasb(?:/|$)")),
    ("translation_other", "unsupported_translation", re.compile(r"^/(?:bab|bib|blb|cg|msb|texts)(?:/|$)")),
    ("bible_context", "unsupported_internal_section", re.compile(r"^/context(?:/|$)")),
    ("bible_book_other", "unsupported_internal_url", re.compile(rf"^/(?:{BOOK_RE})(?:/|$)")),
)
