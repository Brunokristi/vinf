import re

from .base import ExtractorConfig, SectionConfig


CONFIG = ExtractorConfig(
    crawl_group="commentary",
    sections=(
        SectionConfig(
            name="commentary",
            start_patterns=(
                re.compile(r"^EXPOSITORY \(ENGLISH BIBLE\)$", re.IGNORECASE),
            ),
            end_patterns=(
                re.compile(r"^Links$", re.IGNORECASE),
                re.compile(r"^Parallel Commentaries", re.IGNORECASE),
                re.compile(r"^Bible Hub$", re.IGNORECASE),
            ),
        ),
    ),
)
