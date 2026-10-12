from __future__ import annotations

import argparse

from .engine import SearchEngine
from .ui import interactive, print_results, show_detail


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "query",
        nargs="*",
        help="Search query. Omit it to start interactive CLI.",
    )
    parser.add_argument(
        "--idf",
        choices=("classic", "smooth"),
        default="classic",
    )
    parser.add_argument(
        "--mode",
        choices=("or", "and"),
        default=None,
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
        help="Open one result immediately in one-shot mode.",
    )

    return parser


def main() -> None:
    args = build_parser().parse_args()

    engine = SearchEngine()

    try:
        if not args.query:
            interactive(engine)
            return

        query = " ".join(args.query)

        response = engine.search(
            query,
            idf_method=args.idf,
            mode=args.mode,
            limit=args.limit,
            load_sources=True,
        )

        print_results(response)

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


if __name__ == "__main__":
    main()
