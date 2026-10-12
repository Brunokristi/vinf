import re

from .base import ExtractorConfig, SectionConfig


SECONDARY_SECTIONS = (
    re.compile(r"^Strong's Greek$", re.IGNORECASE),
    re.compile(r"^Strong's Hebrew$", re.IGNORECASE),
    re.compile(r"^Greek$", re.IGNORECASE),
    re.compile(r"^Hebrew$", re.IGNORECASE),
    re.compile(r"^Library$", re.IGNORECASE),
    re.compile(r"^Resources$", re.IGNORECASE),
    re.compile(r"^Bible Concordance(?:\s*•.*)?$", re.IGNORECASE),
    re.compile(r"^Subtopics$", re.IGNORECASE),
    re.compile(r"^Related Terms$", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)

REFERENCE_SECTION_END = (
    re.compile(r"^Resources$", re.IGNORECASE),
    re.compile(r"^Library$", re.IGNORECASE),
    re.compile(r"^Bible Concordance(?:\s*•.*)?$", re.IGNORECASE),
    re.compile(r"^Subtopics$", re.IGNORECASE),
    re.compile(r"^Related Terms$", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)

CONFIG = ExtractorConfig(
    crawl_group="topical",
    sections=(
        # Normal contemporary BibleHub topical article.
        SectionConfig(
            name="article",
            start_patterns=(
                re.compile(r"^Topical Encyclopedia(?: Introduction)?:?$", re.IGNORECASE),
            ),
            end_patterns=SECONDARY_SECTIONS,
            required=False,
        ),
        # Some /topical/... pages contain only Nave's material and no
        # Topical Encyclopedia block. Keep that content as a fallback.
        SectionConfig(
            name="naves_index",
            start_patterns=(
                re.compile(r"^Nave's Topical Index$", re.IGNORECASE),
            ),
            end_patterns=REFERENCE_SECTION_END,
            required=False,
        ),
        # Some topical pages are dictionary-style pages rather than a
        # contemporary encyclopedia article (for example "niggardly").
        SectionConfig(
            name="dictionary",
            start_patterns=(
                re.compile(r"^Webster's Revised Unabridged Dictionary$", re.IGNORECASE),
            ),
            end_patterns=SECONDARY_SECTIONS,
            required=False,
        ),
        # Same idea for pages whose useful content is only Torrey's block.
        SectionConfig(
            name="torrey_textbook",
            start_patterns=(
                re.compile(r"^Torrey's Topical Textbook$", re.IGNORECASE),
            ),
            end_patterns=REFERENCE_SECTION_END,
            required=False,
        ),
    ),
    drop_line_patterns=(
        re.compile(r"^Nave's Topical Index$", re.IGNORECASE),
        re.compile(r"^Torrey's Topical Textbook$", re.IGNORECASE),
    ),
)
