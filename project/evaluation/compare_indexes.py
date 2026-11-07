from __future__ import annotations

import argparse
import csv
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lucene_index.engine import LuceneSearchEngine
from searcher.engine import SearchEngine


DEFAULT_OUTPUT_DIR = Path("evaluation/results")

TEST_QUERIES = [
    "moses egypt",
    "jesus resurrection",
    "holy spirit",
    "jerusalem temple",
    "aaron priest",
    "david king",
    "paul faith",
    "abraham covenant",
]


@dataclass
class BackendResult:
    document_id: str
    title: str
    score: float


@dataclass
class EvaluationRow:
    query: str
    mode: str
    top_k: int

    custom_time_ms: float
    lucene_time_ms: float

    overlap_count: int
    overlap_ratio: float

    custom_ids: list[str]
    lucene_ids: list[str]

    custom_titles: list[str]
    lucene_titles: list[str]


def get_value(
    result: Any,
    *names: str,
    default=None,
):
    if isinstance(result, dict):
        for name in names:
            if name in result:
                return result[name]

        return default

    for name in names:
        if hasattr(result, name):
            return getattr(result, name)

    return default


def normalize_custom_result(
    result: Any,
) -> BackendResult:
    document_id = get_value(
        result,
        "document_id",
        "doc_id",
        "id",
        default="",
    )

    title = get_value(
        result,
        "title",
        default="",
    )

    score = get_value(
        result,
        "score",
        default=0.0,
    )

    return BackendResult(
        document_id=str(
            document_id or ""
        ),
        title=str(
            title or ""
        ),
        score=float(
            score or 0.0
        ),
    )


def normalize_lucene_result(
    result,
) -> BackendResult:
    return BackendResult(
        document_id=result.document_id,
        title=result.title,
        score=result.score,
    )


def run_custom_once(
    engine: SearchEngine,
    query: str,
    mode: str,
    top_k: int,
) -> list[BackendResult]:
    response = engine.search(
        query,
        idf_method="classic",
        mode=mode,
        limit=top_k,
        load_sources=True,
    )

    return [
        normalize_custom_result(result)
        for result in response.results
    ]


def run_lucene_once(
    engine: LuceneSearchEngine,
    query: str,
    mode: str,
    top_k: int,
) -> list[BackendResult]:
    results = engine.search(
        query_text=query,
        mode=mode,
        limit=top_k,
        search_fields=["text"],
    )

    return [
        normalize_lucene_result(result)
        for result in results
    ]


def measure(
    function,
    repeats: int,
):
    durations = []
    result = None

    for _ in range(repeats):
        start = time.perf_counter()

        current_result = function()

        elapsed = (
            time.perf_counter()
            - start
        )

        durations.append(
            elapsed * 1000.0
        )

        if result is None:
            result = current_result

    return (
        result,
        statistics.median(
            durations
        ),
    )


def result_key(
    result: BackendResult,
) -> str:
    if result.document_id:
        return result.document_id

    return result.title.lower().strip()


def calculate_overlap(
    custom_results: list[BackendResult],
    lucene_results: list[BackendResult],
    top_k: int,
):
    custom_keys = {
        result_key(result)
        for result in custom_results[:top_k]
    }

    lucene_keys = {
        result_key(result)
        for result in lucene_results[:top_k]
    }

    overlap = (
        custom_keys
        & lucene_keys
    )

    overlap_count = len(
        overlap
    )

    overlap_ratio = (
        overlap_count / top_k
        if top_k > 0
        else 0.0
    )

    return (
        overlap_count,
        overlap_ratio,
    )


def evaluate_query(
    custom_engine: SearchEngine,
    lucene_engine: LuceneSearchEngine,
    query: str,
    mode: str,
    top_k: int,
    repeats: int,
) -> EvaluationRow:
    custom_results, custom_time = measure(
        lambda: run_custom_once(
            custom_engine,
            query,
            mode,
            top_k,
        ),
        repeats,
    )

    lucene_results, lucene_time = measure(
        lambda: run_lucene_once(
            lucene_engine,
            query,
            mode,
            top_k,
        ),
        repeats,
    )

    overlap_count, overlap_ratio = calculate_overlap(
        custom_results,
        lucene_results,
        top_k,
    )

    return EvaluationRow(
        query=query,
        mode=mode,
        top_k=top_k,
        custom_time_ms=custom_time,
        lucene_time_ms=lucene_time,
        overlap_count=overlap_count,
        overlap_ratio=overlap_ratio,
        custom_ids=[
            result.document_id
            for result in custom_results
        ],
        lucene_ids=[
            result.document_id
            for result in lucene_results
        ],
        custom_titles=[
            result.title
            for result in custom_results
        ],
        lucene_titles=[
            result.title
            for result in lucene_results
        ],
    )


def write_csv(
    rows: list[EvaluationRow],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(
            handle
        )

        writer.writerow(
            [
                "query",
                "mode",
                "top_k",
                "custom_time_ms",
                "lucene_time_ms",
                "overlap_count",
                "overlap_ratio",
            ]
        )

        for row in rows:
            writer.writerow(
                [
                    row.query,
                    row.mode,
                    row.top_k,
                    f"{row.custom_time_ms:.3f}",
                    f"{row.lucene_time_ms:.3f}",
                    row.overlap_count,
                    f"{row.overlap_ratio:.3f}",
                ]
            )


def write_markdown(
    rows: list[EvaluationRow],
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as handle:
        handle.write(
            "# Custom index vs. PyLucene\n\n"
        )

        handle.write(
            "Scores are not compared directly because "
            "the custom backend uses TF-IDF/cosine "
            "while Lucene uses its own ranking model.\n\n"
        )

        handle.write(
            "| Query | Mode | Custom ms | "
            "Lucene ms | Top-k overlap |\n"
        )

        handle.write(
            "|---|---:|---:|---:|---:|\n"
        )

        for row in rows:
            handle.write(
                f"| {row.query} "
                f"| {row.mode.upper()} "
                f"| {row.custom_time_ms:.2f} "
                f"| {row.lucene_time_ms:.2f} "
                f"| {row.overlap_count}/{row.top_k} "
                f"({row.overlap_ratio * 100:.1f}%) |\n"
            )

        custom_times = [
            row.custom_time_ms
            for row in rows
        ]

        lucene_times = [
            row.lucene_time_ms
            for row in rows
        ]

        overlap_ratios = [
            row.overlap_ratio
            for row in rows
        ]

        handle.write(
            "\n## Summary\n\n"
        )

        handle.write(
            f"- Average custom query time: "
            f"{statistics.mean(custom_times):.2f} ms\n"
        )

        handle.write(
            f"- Average Lucene query time: "
            f"{statistics.mean(lucene_times):.2f} ms\n"
        )

        handle.write(
            f"- Average top-k overlap: "
            f"{statistics.mean(overlap_ratios) * 100:.1f}%\n"
        )

        handle.write(
            "\n## Top results\n"
        )

        for row in rows:
            handle.write(
                f"\n### {row.query} "
                f"({row.mode.upper()})\n\n"
            )

            handle.write(
                "| Rank | Custom | Lucene |\n"
            )

            handle.write(
                "|---:|---|---|\n"
            )

            count = max(
                len(row.custom_titles),
                len(row.lucene_titles),
            )

            for index in range(count):
                custom_title = (
                    row.custom_titles[index]
                    if index < len(row.custom_titles)
                    else ""
                )

                lucene_title = (
                    row.lucene_titles[index]
                    if index < len(row.lucene_titles)
                    else ""
                )

                custom_title = (
                    custom_title
                    .replace("|", "\\|")
                    .replace("\n", " ")
                )

                lucene_title = (
                    lucene_title
                    .replace("|", "\\|")
                    .replace("\n", " ")
                )

                handle.write(
                    f"| {index + 1} "
                    f"| {custom_title} "
                    f"| {lucene_title} |\n"
                )


def print_summary(
    rows: list[EvaluationRow],
) -> None:
    print()
    print("INDEX COMPARISON")
    print("================")

    print(
        f"{'Query':25} "
        f"{'Mode':5} "
        f"{'Custom ms':>10} "
        f"{'Lucene ms':>10} "
        f"{'Overlap':>10}"
    )

    print(
        "-" * 67
    )

    for row in rows:
        print(
            f"{row.query[:25]:25} "
            f"{row.mode.upper():5} "
            f"{row.custom_time_ms:10.2f} "
            f"{row.lucene_time_ms:10.2f} "
            f"{row.overlap_count:2}/{row.top_k:<7}"
        )

    print()

    custom_average = statistics.mean(
        row.custom_time_ms
        for row in rows
    )

    lucene_average = statistics.mean(
        row.lucene_time_ms
        for row in rows
    )

    overlap_average = statistics.mean(
        row.overlap_ratio
        for row in rows
    )

    print(
        f"Average custom time: "
        f"{custom_average:.2f} ms"
    )

    print(
        f"Average Lucene time: "
        f"{lucene_average:.2f} ms"
    )

    print(
        f"Average top-{rows[0].top_k} overlap: "
        f"{overlap_average * 100:.1f}%"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Compare custom TF-IDF index "
            "with PyLucene."
        )
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
        help=(
            "Number of repetitions used "
            "for median query latency."
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    custom_engine = SearchEngine()
    lucene_engine = LuceneSearchEngine()

    rows = []

    try:
        print("Warming up indexes...")

        run_custom_once(
            custom_engine,
            "moses",
            "or",
            args.top_k,
        )

        run_lucene_once(
            lucene_engine,
            "moses",
            "or",
            args.top_k,
        )

        for query in TEST_QUERIES:
            for mode in (
                "or",
                "and",
            ):
                print(
                    f"Evaluating: "
                    f"{query!r} [{mode.upper()}]"
                )

                row = evaluate_query(
                    custom_engine=custom_engine,
                    lucene_engine=lucene_engine,
                    query=query,
                    mode=mode,
                    top_k=args.top_k,
                    repeats=args.repeats,
                )

                rows.append(
                    row
                )

    finally:
        custom_engine.close()
        lucene_engine.close()

    print_summary(
        rows
    )

    csv_path = (
        args.output
        / "index_comparison.csv"
    )

    markdown_path = (
        args.output
        / "index_comparison.md"
    )

    write_csv(
        rows,
        csv_path,
    )

    write_markdown(
        rows,
        markdown_path,
    )

    print()
    print(
        f"CSV: {csv_path}"
    )

    print(
        f"Markdown: {markdown_path}"
    )


if __name__ == "__main__":
    main()
