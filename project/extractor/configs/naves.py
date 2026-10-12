import re

from .base import ExtractorConfig, SectionConfig


NAVES_MARKER = re.compile(r"^Nave's Topical Index$", re.IGNORECASE)
END_SOURCE = (
    re.compile(r"^Library$", re.IGNORECASE),
    re.compile(r"^Resources$", re.IGNORECASE),
    re.compile(r"^Bible Concordance(?:\s*•.*)?$", re.IGNORECASE),
    re.compile(r"^Subtopics$", re.IGNORECASE),
    re.compile(r"^Related Terms$", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)

CONFIG = ExtractorConfig(
    crawl_group="naves",
    sections=(
        SectionConfig(
            name="article",
            start_patterns=(
                re.compile(r"^Topical Encyclopedia(?: Introduction)?:?$", re.IGNORECASE),
            ),
            end_patterns=(NAVES_MARKER,),
        ),
        SectionConfig(
            name="naves_index",
            start_patterns=(NAVES_MARKER,),
            end_patterns=END_SOURCE,
        ),
    ),
    drop_line_patterns=(NAVES_MARKER,),
)
