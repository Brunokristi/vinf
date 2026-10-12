from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Iterable

from .engine import (
    SearchEngine,
    SearchResponse,
    SearchResult,
)


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
BLUE = "\033[34m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"


def color(
    text: str,
    code: str,
) -> str:
    return f"{code}{text}{RESET}"


def highlight(
    text: str,
    terms: Iterable[str],
) -> str:
    terms = [
        term
        for term in terms
        if term
    ]

    if not terms:
        return text

    pattern = re.compile(
        r"\b("
        + "|".join(
            re.escape(term)
            for term in terms
        )
        + r")\b",
        re.IGNORECASE,
    )

    return pattern.sub(
        lambda match: color(
            match.group(0),
            BOLD + YELLOW,
        ),
        text,
    )


def clean_space(
    text: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        text,
    ).strip()


def make_snippet(
    text: str,
    terms: Iterable[str],
    width: int = 260,
) -> str:
    compact = clean_space(text)

    if not compact:
        return ""

    matches = []

    for term in terms:
        match = re.search(
            rf"\b{re.escape(term)}\b",
            compact,
            re.IGNORECASE,
        )

        if match:
            matches.append(
                match.start()
            )

    if matches:
        center = min(matches)
        start = max(
            0,
            center - width // 3,
        )
    else:
        start = 0

    end = min(
        len(compact),
        start + width,
    )

    snippet = compact[start:end]

    if start > 0:
        snippet = "…" + snippet

    if end < len(compact):
        snippet += "…"

    return snippet


def first_value(
    *values,
):
    for value in values:
        if value not in (
            None,
            "",
        ):
            return value

    return None


def result_title(
    result: SearchResult,
) -> str:
    source = result.source or {}
    catalog = result.catalog or {}

    return str(
        first_value(
            source.get("title"),
            catalog.get("title"),
            source.get("reference"),
            result.document_id,
            f"Document {result.doc_key}",
        )
    )


def result_type(
    result: SearchResult,
) -> str:
    source = result.source or {}
    catalog = result.catalog or {}

    return str(
        first_value(
            source.get("document_type"),
            catalog.get("document_type"),
            catalog.get("type"),
            "document",
        )
    )


def print_results(
    response: SearchResponse,
) -> None:
    print()

    print(
        color(
            f"Results for: {response.query.display}",
            BOLD,
        )
    )

    print(
        f"{response.total_hits:,} matching documents · "
        f"{response.elapsed_seconds * 1000:.2f} ms · "
        f"{response.idf_method} IDF · "
        f"{response.query.mode.upper()}"
    )

    if response.query.ignored_stopwords:
        print(
            color(
                "Ignored stopwords: "
                + ", ".join(
                    response.query.ignored_stopwords
                ),
                DIM,
            )
        )

    print()

    if not response.results:
        print("No results.")
        return

    for result in response.results:
        source = result.source or {}

        title = result_title(
            result
        )

        doc_type = result_type(
            result
        )

        print(
            f"{color(str(result.rank) + '.', BOLD)} "
            f"{color(title, BLUE + BOLD)}"
        )

        if result.document_id:
            print(
                "   "
                + color(
                    f"document:{result.document_id}",
                    GREEN,
                )
            )

        collection = first_value(
            source.get(
                "source_collection"
            ),
            result.catalog.get(
                "source_collection"
            ),
        )

        meta = [
            doc_type,
            f"score {result.score:.6f}",
            "matched "
            + ", ".join(
                result.matched_terms
            ),
        ]

        if collection:
            meta.insert(
                1,
                str(collection),
            )

        print(
            "   "
            + color(
                " · ".join(meta),
                DIM,
            )
        )

        text = str(
            source.get(
                "text",
                "",
            )
        )

        snippet = make_snippet(
            text,
            response.query.terms,
        )

        if snippet:
            print(
                "   "
                + highlight(
                    snippet,
                    response.query.terms,
                )
            )

        print()


def _fmt(
    value: float,
) -> str:
    return f"{value:.12f}"


def render_math_section(
    name: str,
    data: dict,
    n: int,
) -> list[str]:
    lines = []

    lines.append(
        f"{name.upper()} IDF"
    )

    lines.append(
        "-" * 78
    )

    lines.append("")

    if name == "classic":
        lines.append(
            "IDF(t) = ln(N / df(t))"
        )

    else:
        lines.append(
            "IDF(t) = "
            "ln((N + 1) / (df(t) + 1)) + 1"
        )

    lines.append(
        "TFweight(tf) = 1 + ln(tf)"
    )

    lines.append(
        "weight(t,d) = "
        "TFweight(t,d) × IDF(t)"
    )

    lines.append(
        "dot(q,d) = "
        "Σ queryWeight(t) × documentWeight(t)"
    )

    lines.append(
        "score(q,d) = "
        "dot(q,d) / (||q|| × ||d||)"
    )

    lines.append("")

    for row in data["rows"]:
        term = row["term"]

        lines.append(
            f"TERM: {term}"
        )

        lines.append(
            f"  qTF = {row['qtf']}    "
            f"dTF = {row['dtf']}    "
            f"df = {row['df']:,}"
        )

        lines.append(
            f"  qTFweight = "
            f"1 + ln({row['qtf']}) "
            f"= {_fmt(row['qtf_weight'])}"
        )

        if row["dtf"] > 0:
            lines.append(
                f"  dTFweight = "
                f"1 + ln({row['dtf']}) "
                f"= {_fmt(row['dtf_weight'])}"
            )

        else:
            lines.append(
                "  dTFweight = 0"
            )

        if name == "classic":
            lines.append(
                f"  IDF = "
                f"ln({n:,} / {row['df']:,}) "
                f"= {_fmt(row['idf'])}"
            )

        else:
            lines.append(
                f"  IDF = "
                f"ln(({n:,} + 1) / "
                f"({row['df']:,} + 1)) + 1 "
                f"= {_fmt(row['idf'])}"
            )

        lines.append(
            f"  queryWeight = "
            f"{_fmt(row['qtf_weight'])} × "
            f"{_fmt(row['idf'])} "
            f"= {_fmt(row['query_weight'])}"
        )

        lines.append(
            f"  documentWeight = "
            f"{_fmt(row['dtf_weight'])} × "
            f"{_fmt(row['idf'])} "
            f"= {_fmt(row['document_weight'])}"
        )

        lines.append(
            f"  dot contribution = "
            f"{_fmt(row['query_weight'])} × "
            f"{_fmt(row['document_weight'])} "
            f"= {_fmt(row['contribution'])}"
        )

        lines.append("")

    lines.append(
        "dot(q,d) = "
        + " + ".join(
            _fmt(
                row["contribution"]
            )
            for row in data["rows"]
        )
        + f" = {_fmt(data['dot_product'])}"
    )

    lines.append(
        f"||q|| = "
        f"{_fmt(data['query_norm'])}"
    )

    lines.append(
        f"||d|| = "
        f"{_fmt(data['document_norm'])}"
    )

    lines.append(
        f"denominator = "
        f"{_fmt(data['query_norm'])} × "
        f"{_fmt(data['document_norm'])} "
        f"= {_fmt(data['denominator'])}"
    )

    lines.append(
        f"score = "
        f"{_fmt(data['dot_product'])} / "
        f"{_fmt(data['denominator'])} "
        f"= {_fmt(data['score'])}"
    )

    lines.append("")

    return lines


def render_detail(
    engine: SearchEngine,
    response: SearchResponse,
    result: SearchResult,
) -> str:
    source = (
        engine.get_source_document(result)
        or {}
    )

    explanation = engine.explain(
        response,
        result,
    )

    lines = []

    title = result_title(result)

    # =========================================================
    # TITLE
    # =========================================================

    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")

    # =========================================================
    # SEARCH SUMMARY
    # =========================================================

    lines.append("SEARCH")
    lines.append("-" * 78)

    lines.append(
        f"Original query:      "
        f"{response.query.original}"
    )

    lines.append(
        f"Search terms:        "
        f"{', '.join(response.query.terms)}"
    )

    if response.query.ignored_stopwords:
        lines.append(
            "Ignored stopwords:   "
            + ", ".join(
                response.query.ignored_stopwords
            )
        )

    lines.append(
        f"Parsed query:        "
        f"{response.query.display}"
    )

    lines.append(
        f"Boolean mode:        "
        f"{response.query.mode.upper()}"
    )

    lines.append(
        f"Result rank:         "
        f"#{result.rank}"
    )

    lines.append(
        f"Matching documents:  "
        f"{response.total_hits:,}"
    )

    lines.append(
        f"Selected IDF:        "
        f"{response.idf_method}"
    )

    lines.append(
        f"Score:               "
        f"{result.score:.12f}"
    )

    lines.append(
        "Matched terms:       "
        + ", ".join(
            result.matched_terms
        )
    )

    # =========================================================
    # EXTRACTED DOCUMENT
    # =========================================================

    lines.append("")
    lines.append("EXTRACTED DOCUMENT")
    lines.append("=" * 78)
    lines.append("")

    text = str(
        source.get(
            "text",
            "",
        )
    )

    if text:
        lines.append(
            highlight(
                text,
                response.query.terms,
            )
        )
    else:
        lines.append(
            "[No extracted text available]"
        )

    lines.append("")

    # =========================================================
    # DOCUMENT METADATA
    # =========================================================

    lines.append("DOCUMENT METADATA")
    lines.append("=" * 78)

    preferred_fields = (
        "document_id",
        "document_type",
        "source_collection",
        "crawl_group",
        "title",
        "book",
        "chapter",
        "verse",
        "reference",
        "topic",
        "place",
        "text_length",
        "word_count",
        "text_hash",
    )

    shown = set()

    for field in preferred_fields:
        if field not in source:
            continue

        value = source[field]

        lines.append(
            f"{field:20s} {value}"
        )

        shown.add(field)

    lines.append(
        f"{'index_doc':20s} "
        f"{result.doc_key}"
    )

    original_url = (
        source.get("url")
        or result.catalog.get("url")
    )

    if original_url:
        lines.append("")
        lines.append("ORIGINAL SOURCE")
        lines.append("-" * 78)
        lines.append(str(original_url))

    lines.append("")

    # =========================================================
    # RANKING MATHEMATICS
    # =========================================================

    lines.append("RANKING MATHEMATICS")
    lines.append("=" * 78)
    lines.append("")

    lines.append(
        "These values are the same TF, IDF, vector weights "
        "and document norms used by the search engine."
    )

    lines.append("")

    for method in (
        "classic",
        "smooth",
    ):
        lines.extend(
            render_math_section(
                method,
                explanation["methods"][method],
                explanation["document_count"],
            )
        )

    # =========================================================
    # SCORE COMPARISON
    # =========================================================

    lines.append("SCORE COMPARISON")
    lines.append("=" * 78)

    lines.append(
        "Classic: "
        f"{explanation['methods']['classic']['score']:.12f}"
    )

    lines.append(
        "Smooth:  "
        f"{explanation['methods']['smooth']['score']:.12f}"
    )

    lines.append("")

    # =========================================================
    # ADDITIONAL METADATA
    # =========================================================

    extra_metadata = {
        key: value
        for key, value in source.items()
        if key not in shown
        and key not in {
            "text",
            "sections",
            "verses",
            "url",
        }
    }

    if extra_metadata:
        lines.append(
            "ADDITIONAL EXTRACTED METADATA"
        )

        lines.append(
            "=" * 78
        )

        lines.append(
            json.dumps(
                extra_metadata,
                indent=4,
                ensure_ascii=False,
            )
        )

        lines.append("")

    return "\n".join(lines)

def show_detail(
    engine: SearchEngine,
    response: SearchResponse,
    result: SearchResult,
) -> None:
    content = render_detail(
        engine,
        response,
        result,
    )

    if shutil.which("less"):
        env = os.environ.copy()

        env["LESS"] = (
            "-R -F -X"
        )

        subprocess.run(
            [
                "less",
                "-R",
            ],
            input=content,
            text=True,
            env=env,
            check=False,
        )

        return

    print(
        content
    )


HELP = """
Commands
--------
<query>          search, e.g. moses and egypt
1..N             open a result
:idf classic     use classic IDF
:idf smooth      use smooth IDF
:mode and        force AND
:mode or         force OR
:mode auto       infer AND/OR from query text
:limit 20        change result limit
:help            show help
:quit            quit

Examples
--------
moses and egypt
joseph in egypt
david or solomon
jerusalem temple
"""


def interactive(
    engine: SearchEngine,
) -> None:
    idf = "classic"
    forced_mode = None
    limit = 10
    last_response = None

    print()

    print(
        color(
            "Biblical Search Engine",
            BOLD + BLUE,
        )
    )

    print(
        f"{engine.document_count:,} documents · "
        f"{len(engine.lexicon):,} terms"
    )

    print(
        "Type :help for commands."
    )

    print()

    while True:
        try:
            raw = input(
                color(
                    "search> ",
                    CYAN + BOLD,
                )
            ).strip()

        except (
            EOFError,
            KeyboardInterrupt,
        ):
            print()
            break

        if not raw:
            continue

        if raw in {
            ":quit",
            ":q",
            "quit",
            "exit",
        }:
            break

        if raw == ":help":
            print(
                HELP
            )

            continue

        if raw.startswith(
            ":idf "
        ):
            value = (
                raw.split(
                    maxsplit=1
                )[1]
                .strip()
                .lower()
            )

            if value not in {
                "classic",
                "smooth",
            }:
                print(
                    "Use: "
                    ":idf classic | "
                    ":idf smooth"
                )

                continue

            idf = value

            print(
                f"IDF set to {idf}."
            )

            continue

        if raw.startswith(
            ":mode "
        ):
            value = (
                raw.split(
                    maxsplit=1
                )[1]
                .strip()
                .lower()
            )

            if value == "auto":
                forced_mode = None

            elif value in {
                "and",
                "or",
            }:
                forced_mode = value

            else:
                print(
                    "Use: "
                    ":mode and | "
                    ":mode or | "
                    ":mode auto"
                )

                continue

            print(
                "Mode set to "
                + (
                    forced_mode.upper()
                    if forced_mode
                    else "AUTO"
                )
                + "."
            )

            continue

        if raw.startswith(
            ":limit "
        ):
            try:
                value = int(
                    raw.split(
                        maxsplit=1
                    )[1]
                )

                if (
                    value < 1
                    or value > 100
                ):
                    raise ValueError

            except ValueError:
                print(
                    "Limit must be "
                    "between 1 and 100."
                )

                continue

            limit = value

            print(
                f"Limit set to {limit}."
            )

            continue

        if (
            raw.isdigit()
            and last_response is not None
        ):
            number = int(
                raw
            )

            if (
                1
                <= number
                <= len(
                    last_response.results
                )
            ):
                show_detail(
                    engine,
                    last_response,
                    last_response.results[
                        number - 1
                    ],
                )

            else:
                print(
                    f"Choose a result between "
                    f"1 and "
                    f"{len(last_response.results)}."
                )

            continue

        try:
            last_response = engine.search(
                raw,
                idf_method=idf,
                mode=forced_mode,
                limit=limit,
                load_sources=True,
            )

            print_results(
                last_response
            )

            print(
                color(
                    "Enter a result number "
                    "to open the extracted document, "
                    "or type another query.",
                    DIM,
                )
            )

        except Exception as exc:
            print(
                color(
                    f"Error: {exc}",
                    YELLOW,
                )
            )