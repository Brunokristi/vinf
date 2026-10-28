from __future__ import annotations

from html import unescape
import re

from .configs.base import ExtractorConfig

COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
DROP_ELEMENT_RE = re.compile(
    r"<(script|style|noscript|iframe|svg|canvas|form|select|button)\b[^>]*>"
    r".*?</\1\s*>",
    re.IGNORECASE | re.DOTALL,
)
FOOTNOTE_MARKER_RE = re.compile(
    r'''<span\b[^>]*class=["'][^"']*\bfn\b[^"']*["'][^>]*>.*?</span\s*>''',
    re.IGNORECASE | re.DOTALL,
)
BLOCK_TAG_RE = re.compile(
    r"</?(?:p|div|br|li|ul|ol|h[1-6]|tr|td|th|table|section|article|"
    r"header|footer|nav|blockquote|hr)\b[^>]*>",
    re.IGNORECASE,
)
TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
TITLE_RE = re.compile(r"<title\b[^>]*>(.*?)</title\s*>", re.IGNORECASE | re.DOTALL)
SPACE_RE = re.compile(r"[ \t\r\f\v]+")
BLANK_LINES_RE = re.compile(r"\n{2,}")
ZERO_WIDTH_RE = re.compile(r"[\u200b\u2060\ufeff]+")


def normalize_line(value: str) -> str:
    value = value.replace("\u00ad", "")
    value = ZERO_WIDTH_RE.sub(" ", value)
    return SPACE_RE.sub(" ", value).strip()


def _strip_tags(value: str) -> str:
    return normalize_line(unescape(TAG_RE.sub("", value)))


def html_title(html: str) -> str | None:
    match = TITLE_RE.search(html)
    if match is None:
        return None
    title = _strip_tags(match.group(1))
    return title or None


def html_to_lines(html: str, config: ExtractorConfig) -> list[str]:

    value = html

    for pattern, replacement in config.html_substitutions:
        value = pattern.sub(replacement, value)

    value = COMMENT_RE.sub("\n", value)
    value = DROP_ELEMENT_RE.sub("\n", value)
    value = FOOTNOTE_MARKER_RE.sub("", value)

    # Preserve visible block boundaries before removing all remaining tags.
    value = BLOCK_TAG_RE.sub("\n", value)
    value = TAG_RE.sub("", value)
    value = unescape(value)
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = BLANK_LINES_RE.sub("\n", value)

    lines: list[str] = []
    previous: str | None = None

    for raw_line in value.split("\n"):
        line = normalize_line(raw_line)
        if not line:
            continue
        if line == previous:
            continue
        lines.append(line)
        previous = line

    return lines
