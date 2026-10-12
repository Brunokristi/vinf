import re

from .base import ExtractorConfig, SectionConfig


# A tiny number of BibleHub commentary pages are minified/collapsed so that
# the section labels are glued to neighbouring inline HTML. These substitutions
# insert text boundaries BEFORE tag stripping; the actual extraction is still
# done by the regex section rules below.
RAW_START_BOUNDARY = re.compile(
    r"(EXPOSITORY\s*\(ENGLISH BIBLE\))(?=\s*<)",
    re.IGNORECASE,
)
RAW_END_BOUNDARY = re.compile(
    r"(?<![A-Za-z])(Links)(?=\s*<)",
    re.IGNORECASE,
)


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
    html_substitutions=(
        (RAW_START_BOUNDARY, r"\n\1\n"),
        (RAW_END_BOUNDARY, r"\n\1\n"),
    ),
)
