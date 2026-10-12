import re

from .base import ExtractorConfig, SectionConfig


TORREY_MARKER = re.compile(r"^Torrey's Topical Textbook$", re.IGNORECASE)
END_SOURCE = (
    re.compile(r"^Library$", re.IGNORECASE),
    re.compile(r"^Resources$", re.IGNORECASE),
    re.compile(r"^Bible Concordance(?:\s*•.*)?$", re.IGNORECASE),
    re.compile(r"^Subtopics$", re.IGNORECASE),
    re.compile(r"^Related Terms$", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)

CONFIG = ExtractorConfig(
    crawl_group="torrey",
    sections=(
        SectionConfig(
            name="article",
            start_patterns=(
                re.compile(r"^Topical Encyclopedia(?: Introduction)?:?$", re.IGNORECASE),
            ),
            end_patterns=(TORREY_MARKER,),
        ),
        SectionConfig(
            name="torrey_textbook",
            start_patterns=(TORREY_MARKER,),
            end_patterns=END_SOURCE,
        ),
    ),
    drop_line_patterns=(TORREY_MARKER,),
)
