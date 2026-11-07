from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from pathlib import Path

from lucene_index.engine import LuceneSearchEngine


DEFAULT_OUTPUT = Path(
    "evaluation/results/lucene_features.md"
)


@dataclass
class FeatureTest:
    name: str
    description: str
    query: str
    kwargs: dict


@dataclass
class FeatureResult:
    name: str
    description: str
    query: str
    time_ms: float
    count: int
    titles: list[str]


TESTS = [
    FeatureTest(
        name="Phrase",
        description=(
            "Exact phrase search over Lucene text fields."
        ),
        query="holy spirit",
        kwargs={
            "phrase": True,
        },
    ),
    FeatureTest(
        name="Fuzzy",
        description=(
            "Typo-tolerant search using edit distance 1."
        ),
        query="jeruslem",
        kwargs={
            "fuzzy": 1,
        },
    ),
    FeatureTest(
        name="Boolean AND",
        description=(
            "Both query terms must occur in the document."
        ),
        query="moses egypt",
        kwargs={
            "mode": "and",
        },
    ),
    FeatureTest(
        name="Boolean OR",
        description=(
            "At least one query term may occur in the document."
        ),
        query="moses egypt",
        kwargs={
            "mode": "or",
        },
    ),
    FeatureTest(
        name="Field filter",
        description=(
            "Full-text search restricted to the commentary crawl group."
        ),
        query="moses",
        kwargs={
            "group": "commentary",
        },
    ),
    FeatureTest(
        name="Book filter",
        description=(
            "Full-text search restricted to the Book of John."
        ),
        query="jesus",
        kwargs={
            "book": "John",
        },
    ),
    FeatureTest(
        name="Chapter range",
        description=(
            "Full-text search restricted to chapters 1 through 10."
        ),
        query="jesus",
        kwargs={
            "book": "John",
            "chapter_min": 1,
            "chapter_max": 10,
        },
    ),
    FeatureTest(
        name="Wikipedia reference range",
        description=(
            "Search only documents enriched from Wikipedia pages "
            "with at least 20 references."
        ),
        query="moses",
        kwargs={
            "wiki_refs_min": 20,
        },
    ),
    FeatureTest(
        name="Combined query",
        description=(
            "Boolean AND search combined with a crawl-group filter."
        ),
        query="moses egypt",
        kwargs={
            "mode": "and",
            "group": "naves",
        },
    ),
]


def run_once(
    engine: LuceneSearchEngine,
    test: FeatureTest,
    limit: int,
):
    return engine.search(
        query_text=test.query,
        limit=limit,
        **test.kwargs,
    )


def measure_test(
    engine: LuceneSearchEngine,
    test: FeatureTest,
    limit: int,
    repeats: int,
) -> FeatureResult:
    durations = []
    final_results = []

    for _ in range(repeats):
        start = time.perf_counter()

        results = run_once(
            engine,
            test,
            limit,
        )

        elapsed = (
            time.perf_counter()
            - start
        ) * 1000.0

        durations.append(
            elapsed
        )

        final_results = results

    return FeatureResult(
        name=test.name,
        description=test.description,
        query=test.query,
        time_ms=statistics.median(
            durations
        ),
        count=len(
            final_results
        ),
        titles=[
            result.title
            for result in final_results
        ],
    )


def print_results(
    results: list[FeatureResult],
) -> None:
    print()
    print("LUCENE FEATURE EVALUATION")
    print("=========================")

    print(
        f"{'Feature':30} "
        f"{'Time ms':>10} "
        f"{'Shown':>7}"
    )

    print(
        "-" * 51
    )

    for result in results:
        print(
            f"{result.name[:30]:30} "
            f"{result.time_ms:10.2f} "
            f"{result.count:7}"
        )

    print()

    average = statistics.mean(
        result.time_ms
        for result in results
    )

    print(
        f"Average feature query time: "
        f"{average:.2f} ms"
    )


def write_markdown(
    results: list[FeatureResult],
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
            "# PyLucene feature evaluation\n\n"
        )

        handle.write(
            "The following tests demonstrate query types "
            "that are available in the PyLucene backend.\n\n"
        )

        handle.write(
            "| Feature | Query | Median time | Results shown |\n"
        )

        handle.write(
            "|---|---|---:|---:|\n"
        )

        for result in results:
            handle.write(
                f"| {result.name} "
                f"| `{result.query}` "
                f"| {result.time_ms:.2f} ms "
                f"| {result.count} |\n"
            )

        average = statistics.mean(
            result.time_ms
            for result in results
        )

        handle.write(
            "\n"
            f"Average query time: "
            f"**{average:.2f} ms**.\n"
        )

        handle.write(
            "\n## Individual tests\n"
        )

        for result in results:
            handle.write(
                f"\n### {result.name}\n\n"
            )

            handle.write(
                f"{result.description}\n\n"
            )

            handle.write(
                f"Query: `{result.query}`\n\n"
            )

            handle.write(
                f"Median time: "
                f"**{result.time_ms:.2f} ms**\n\n"
            )

            handle.write(
                "Top results:\n\n"
            )

            for rank, title in enumerate(
                result.titles,
                start=1,
            ):
                safe_title = (
                    title
                    .replace("\n", " ")
                )

                handle.write(
                    f"{rank}. {safe_title}\n"
                )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate advanced PyLucene query features."
        )
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--repeats",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    engine = LuceneSearchEngine()

    results = []

    try:
        print(
            "Warming up Lucene..."
        )

        engine.search(
            "moses",
            limit=args.limit,
        )

        for test in TESTS:
            print(
                f"Evaluating: "
                f"{test.name}"
            )

            result = measure_test(
                engine=engine,
                test=test,
                limit=args.limit,
                repeats=args.repeats,
            )

            results.append(
                result
            )

    finally:
        engine.close()

    print_results(
        results
    )

    write_markdown(
        results,
        args.output,
    )

    print()
    print(
        f"Markdown: {args.output}"
    )


if __name__ == "__main__":
    main()
