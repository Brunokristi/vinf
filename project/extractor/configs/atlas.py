import re

from .base import ExtractorConfig, SectionConfig


ENCYCLOPEDIA = re.compile(r"^Encyclopedia$", re.IGNORECASE)
STRONGS_OR_END = (
    re.compile(r"^Strong's Greek$", re.IGNORECASE),
    re.compile(r"^Strong's Hebrew$", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)

CONFIG = ExtractorConfig(
    crawl_group="atlas",
    sections=(
        SectionConfig(
            name="occurrences",
            start_patterns=(
                re.compile(r"^Occurrences$", re.IGNORECASE),
            ),
            end_patterns=(ENCYCLOPEDIA,),
            required=False,
        ),
        SectionConfig(
            name="encyclopedia",
            start_patterns=(ENCYCLOPEDIA,),
            end_patterns=STRONGS_OR_END,
            required=False,
        ),
    ),
)
