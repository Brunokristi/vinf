from __future__ import annotations

import argparse
from pathlib import Path

from lucene_index.engine import LuceneSearchEngine


DEFAULT_INDEX = Path("data/lucene_index")


def print_results(results) -> None:
    for rank, result in enumerate(
        results,
        start=1,
    ):
        print(
            f"{rank}. "
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


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Search BibleHub using PyLucene."
        )
    )

    parser.add_argument(
        "query",
        help="Search query.",
    )

    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--mode",
        choices=[
            "and",
            "or",
        ],
        default="or",
    )

    parser.add_argument(
        "--phrase",
        action="store_true",
    )

    parser.add_argument(
        "--fuzzy",
        type=int,
        choices=[
            1,
            2,
        ],
    )

    parser.add_argument(
        "--group",
        choices=[
            "atlas",
            "bible",
            "commentary",
            "naves",
            "topical",
            "torrey",
        ],
    )

    parser.add_argument(
        "--book",
    )

    parser.add_argument(
        "--document-type",
    )

    parser.add_argument(
        "--chapter-min",
        type=int,
    )

    parser.add_argument(
        "--chapter-max",
        type=int,
    )

    parser.add_argument(
        "--verse-min",
        type=int,
    )

    parser.add_argument(
        "--verse-max",
        type=int,
    )

    parser.add_argument(
        "--wiki-refs-min",
        type=int,
    )

    parser.add_argument(
        "--wiki-refs-max",
        type=int,
    )

    args = parser.parse_args()

    if (
        args.phrase
        and args.fuzzy is not None
    ):
        parser.error(
            "--phrase and --fuzzy "
            "cannot be used together."
        )

    if (
        args.chapter_min is not None
        and args.chapter_max is not None
        and args.chapter_min
        > args.chapter_max
    ):
        parser.error(
            "--chapter-min cannot be greater "
            "than --chapter-max."
        )

    if (
        args.verse_min is not None
        and args.verse_max is not None
        and args.verse_min
        > args.verse_max
    ):
        parser.error(
            "--verse-min cannot be greater "
            "than --verse-max."
        )

    if (
        args.wiki_refs_min is not None
        and args.wiki_refs_max is not None
        and args.wiki_refs_min
        > args.wiki_refs_max
    ):
        parser.error(
            "--wiki-refs-min cannot be greater "
            "than --wiki-refs-max."
        )

    return args


def main() -> None:
    args = parse_args()

    engine = LuceneSearchEngine(
        index_path=args.index,
    )

    try:
        results = engine.search(
            query_text=args.query,
            limit=args.limit,
            mode=args.mode,
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

        print_results(
            results
        )

    finally:
        engine.close()


if __name__ == "__main__":
    main()