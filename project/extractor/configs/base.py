from __future__ import annotations

from dataclasses import dataclass, field
import re


Pattern = re.Pattern[str]


@dataclass(frozen=True)
class SectionConfig:
    name: str
    start_patterns: tuple[Pattern, ...]
    end_patterns: tuple[Pattern, ...]
    include_start: bool = False
    required: bool = True


@dataclass(frozen=True)
class ExtractorConfig:
    crawl_group: str
    sections: tuple[SectionConfig, ...] = ()
    drop_line_patterns: tuple[Pattern, ...] = ()
    html_substitutions: tuple[tuple[Pattern, str], ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
