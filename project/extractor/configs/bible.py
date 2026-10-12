import re

from .base import ExtractorConfig


# BibleHub renders verse numbers inside a stable reftext span. Replace those
# spans with a sentinel before stripping the rest of the HTML tags. This keeps
# verse boundaries explicit while still using only regular expressions.
VERSE_SPAN = re.compile(
    r'''<span\b[^>]*class=["'][^"']*\breftext\b[^"']*["'][^>]*>'''
    r'''.*?<b>\s*(\d{1,3})\s*</b>.*?</span\s*>''',
    re.IGNORECASE | re.DOTALL,
)

CONFIG = ExtractorConfig(
    crawl_group="bible",
    html_substitutions=(
        (VERSE_SPAN, r"\n@@VERSE:\1@@\n"),
    ),
    drop_line_patterns=(
        re.compile(r"^Footnotes:?$", re.IGNORECASE),
    ),
)

END_PATTERNS = (
    re.compile(r"^Footnotes:?$", re.IGNORECASE),
    re.compile(r"^Berean Standard Bible \(BSB\)", re.IGNORECASE),
    re.compile(r"^Bible Hub$", re.IGNORECASE),
)

VERSE_SENTINEL = re.compile(r"^@@VERSE:(\d{1,3})@@$")
