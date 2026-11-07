from __future__ import annotations

import argparse
from pathlib import Path

from .engine import SearchEngine
from .ui import interactive, print_results, show_detail


DEFAULT_LUCENE_INDEX = Path("data/lucene_index")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="BibleHub search application.",
    )

    parser.add_argument(
        "query",
        nargs="*",
        help="Search query. Omit it to start interactive CLI.",
    )

    parser.add_argument(
        "--backend",
        choices=("custom", "lucene"),
        default="lucene",
        help=(
            "Search backend. "
            "Default: lucene."
        ),
    )

    parser.add_argument(
        "--idf",
        choices=("classic", "smooth"),
        default="classic",
        help=(
            "IDF method for the custom backend."
        ),
    )

    parser.add_argument(
        "--mode",
        choices=("or", "and"),
        default=None,
        help=(
            "Boolean query mode. "
            "Default is backend-specific."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--open",
        type=int,
        default=None,
        dest="open_result",
        help=(
            "Open one result immediately. "
            "Supported by the custom backend."
        ),
    )

    parser.add_argument(
        "--phrase",
        action="store_true",
        help=(
            "Lucene only: search the query "
            "as an exact phrase."
        ),
    )

    parser.add_argument(
        "--fuzzy",
        type=int,
        choices=(1, 2),
        help=(
            "Lucene only: fuzzy search with "
            "maximum edit distance 1 or 2."
        ),
    )

    parser.add_argument(
        "--group",
        choices=(
            "atlas",
            "bible",
            "commentary",
            "naves",
            "topical",
            "torrey",
        ),
        help=(
            "Lucene only: filter by crawl group."
        ),
    )

    parser.add_argument(
        "--book",
        help=(
            "Lucene only: exact Bible book filter."
        ),
    )

    parser.add_argument(
        "--document-type",
        help=(
            "Lucene only: exact document type filter."
        ),
    )

    parser.add_argument(
        "--chapter-min",
        type=int,
        help=(
            "Lucene only: minimum chapter."
        ),
    )

    parser.add_argument(
        "--chapter-max",
        type=int,
        help=(
            "Lucene only: maximum chapter."
        ),
    )

    parser.add_argument(
        "--verse-min",
        type=int,
        help=(
            "Lucene only: minimum verse."
        ),
    )

    parser.add_argument(
        "--verse-max",
        type=int,
        help=(
            "Lucene only: maximum verse."
        ),
    )

    parser.add_argument(
        "--wiki-refs-min",
        type=int,
        help=(
            "Lucene only: minimum Wikipedia "
            "reference count."
        ),
    )

    parser.add_argument(
        "--wiki-refs-max",
        type=int,
        help=(
            "Lucene only: maximum Wikipedia "
            "reference count."
        ),
    )

    parser.add_argument(
        "--lucene-index",
        type=Path,
        default=DEFAULT_LUCENE_INDEX,
        help=(
            "Path to the Lucene index."
        ),
    )

    return parser


def validate_args(
    parser: argparse.ArgumentParser,
    args: argparse.Namespace,
) -> None:
    if (
        args.phrase
        and args.fuzzy is not None
    ):
        parser.error(
            "--phrase and --fuzzy cannot "
            "be used together."
        )

    if (
        args.chapter_min is not None
        and args.chapter_max is not None
        and args.chapter_min > args.chapter_max
    ):
        parser.error(
            "--chapter-min cannot be greater "
            "than --chapter-max."
        )

    if (
        args.verse_min is not None
        and args.verse_max is not None
        and args.verse_min > args.verse_max
    ):
        parser.error(
            "--verse-min cannot be greater "
            "than --verse-max."
        )

    if (
        args.wiki_refs_min is not None
        and args.wiki_refs_max is not None
        and args.wiki_refs_min > args.wiki_refs_max
    ):
        parser.error(
            "--wiki-refs-min cannot be greater "
            "than --wiki-refs-max."
        )

    if (
        args.backend == "custom"
        and (
            args.phrase
            or args.fuzzy is not None
            or args.group is not None
            or args.book is not None
            or args.document_type is not None
            or args.chapter_min is not None
            or args.chapter_max is not None
            or args.verse_min is not None
            or args.verse_max is not None
            or args.wiki_refs_min is not None
            or args.wiki_refs_max is not None
        )
    ):
        parser.error(
            "Phrase, fuzzy, field and range "
            "queries require --backend lucene."
        )

    if (
        args.backend == "lucene"
        and args.open_result is not None
    ):
        parser.error(
            "--open is currently supported "
            "only by --backend custom."
        )


def print_lucene_results(
    results,
) -> None:
    for number, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{number}. "
            f"[score={result.score:.4f}] "
            f"{result.title}"
        )

        if result.crawl_group:
            print(
                f"   group: {result.crawl_group}"
            )

        if result.document_id:
            print(
                f"   id: {result.document_id}"
            )

        if result.book:
            print(
                f"   book: {result.book}"
            )

        if result.chapter is not None:
            print(
                f"   chapter: {result.chapter}"
            )

        if result.verse is not None:
            print(
                f"   verse: {result.verse}"
            )

        if result.topic:
            print(
                f"   topic: {result.topic}"
            )

        if result.place:
            print(
                f"   place: {result.place}"
            )

        if result.wiki_title:
            print(
                f"   wiki: {result.wiki_title}"
            )

        if result.preview:
            print(
                f"   {result.preview[:300]}"
            )

        if result.url:
            print(
                f"   {result.url}"
            )

        print()


def run_custom(
    args: argparse.Namespace,
    query: str,
) -> None:
    engine = SearchEngine()

    try:
        response = engine.search(
            query,
            idf_method=args.idf,
            mode=args.mode,
            limit=args.limit,
            load_sources=True,
        )

        print_results(
            response
        )

        if args.open_result is not None:
            number = args.open_result

            if not 1 <= number <= len(response.results):
                raise SystemExit(
                    f"--open must be between 1 and "
                    f"{len(response.results)}."
                )

            show_detail(
                engine,
                response,
                response.results[number - 1],
            )

    finally:
        engine.close()


def run_lucene(
    args: argparse.Namespace,
    query: str,
) -> None:
    from lucene_index.engine import LuceneSearchEngine

    engine = LuceneSearchEngine(
        index_path=args.lucene_index,
    )

    try:
        results = engine.search(
            query_text=query,
            limit=args.limit,
            mode=args.mode or "or",
            phrase=args.phrase,
            fuzzy=args.fuzzy,
            group=args.group,
            book=args.book,
            document_type=args.document_type,
            chapter_min=args.chapter_min,
            chapter_max=args.chapter_max,
            verse_min=args.verse_min,
            verse_max=args.verse_max,
            wiki_refs_min=args.wiki_refs_min,
            wiki_refs_max=args.wiki_refs_max,
        )

        print()
        print("Backend: PyLucene")
        print(f"Query: {query}")
        print(
            f"Mode: "
            f"{'phrase' if args.phrase else 'fuzzy' if args.fuzzy is not None else args.mode or 'or'}"
        )
        print(f"Results shown: {len(results)}")
        print()

        print_lucene_results(
            results
        )

    finally:
        engine.close()


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    validate_args(
        parser,
        args,
    )

    if not args.query:
        if args.backend == "lucene":
            raise SystemExit(
                "Interactive mode currently uses the custom backend. "
                "Use --backend custom without a query, or provide "
                "a query for the Lucene backend."
            )

        engine = SearchEngine()

        try:
            interactive(
                engine
            )
        finally:
            engine.close()

        return

    query = " ".join(
        args.query
    )

    if args.backend == "lucene":
        run_lucene(
            args,
            query,
        )
    else:
        run_custom(
            args,
            query,
        )


if __name__ == "__main__":
    main()