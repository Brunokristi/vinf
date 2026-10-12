from __future__ import annotations

from dataclasses import dataclass, field
import re


Pattern = re.Pattern[str]


@dataclass(frozen=True)
class SectionConfig:
    """One relevant text section inside a page.

    start_patterns and end_patterns are matched against already-cleaned text lines.
    The start marker itself is excluded by default. The first matching end marker
    after the start is also excluded.
    """

    name: str
    start_patterns: tuple[Pattern, ...]
    end_patterns: tuple[Pattern, ...]
    include_start: bool = False
    required: bool = True


@dataclass(frozen=True)
class ExtractorConfig:
    """Editable extraction rules for one crawl group."""

    crawl_group: str
    sections: tuple[SectionConfig, ...] = ()
    drop_line_patterns: tuple[Pattern, ...] = ()
    html_substitutions: tuple[tuple[Pattern, str], ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
