from __future__ import annotations

import re

from .configs.base import ExtractorConfig, SectionConfig
from .regex_html import html_to_lines


def matches_any(line: str, patterns: tuple[re.Pattern[str], ...]) -> bool:
    return any(pattern.search(line) for pattern in patterns)


def find_first(
    lines: list[str],
    patterns: tuple[re.Pattern[str], ...],
    start: int = 0,
) -> int | None:
    for index in range(start, len(lines)):
        if matches_any(lines[index], patterns):
            return index
    return None


def extract_section(lines: list[str], section: SectionConfig) -> list[str]:
    start_marker = find_first(lines, section.start_patterns)

    if start_marker is None:
        if section.required:
            return []
        return []

    start = start_marker if section.include_start else start_marker + 1
    end_marker = find_first(lines, section.end_patterns, start=start)
    end = end_marker if end_marker is not None else len(lines)
    return lines[start:end]


def clean_lines(lines: list[str], config: ExtractorConfig) -> list[str]:
    cleaned: list[str] = []
    previous: str | None = None

    for line in lines:
        if matches_any(line, config.drop_line_patterns):
            continue
        if line in {"•", "|", "◄", "►", "Par ▾", "iframe"}:
            continue
        if line == previous:
            continue
        cleaned.append(line)
        previous = line

    return cleaned


def extract_configured_sections(
    html: str,
    config: ExtractorConfig,
) -> tuple[dict[str, str], list[str]]:
    lines = html_to_lines(html, config)
    extracted: dict[str, str] = {}
    all_parts: list[str] = []

    for section in config.sections:
        section_lines = clean_lines(extract_section(lines, section), config)
        text = "\n".join(section_lines).strip()
        extracted[section.name] = text
        if text:
            all_parts.extend(section_lines)

    return extracted, clean_lines(all_parts, config)


def lines_to_text(lines: list[str]) -> str:
    return "\n".join(lines).strip()
