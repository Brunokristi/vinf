from __future__ import annotations

import re
from pathlib import Path

import lucene

from java.nio.file import Paths

from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import IntPoint
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.index import Term
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.search import BooleanClause
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import FuzzyQuery
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search import MatchAllDocsQuery
from org.apache.lucene.search import TermQuery
from org.apache.lucene.store import FSDirectory

from searcher.result import SearchResult


DEFAULT_INDEX = Path("data/lucene_index")

SEARCH_FIELDS = [
    "title",
    "text",
    "topic",
    "place",
    "wiki_title",
    "wiki_categories",
    "wiki_sections",
    "wiki_bold_terms",
]


def normalize_terms(query_text: str) -> list[str]:
    return re.findall(
        r"[A-Za-z0-9]+",
        query_text.lower(),
    )


def build_field_query(
    text: str,
    field: str,
    analyzer: StandardAnalyzer,
):
    parser = QueryParser(
        field,
        analyzer,
    )

    return parser.parse(
        QueryParser.escape(text)
    )


def build_phrase_query(
    query_text: str,
    analyzer: StandardAnalyzer,
    search_fields: list[str],
):
    builder = BooleanQuery.Builder()

    escaped = QueryParser.escape(
        query_text.strip()
    )

    phrase_text = f'"{escaped}"'

    for field in search_fields:
        parser = QueryParser(
            field,
            analyzer,
        )

        field_query = parser.parse(
            phrase_text
        )

        builder.add(
            field_query,
            BooleanClause.Occur.SHOULD,
        )

    return builder.build()


def build_boolean_query(
    query_text: str,
    analyzer: StandardAnalyzer,
    mode: str,
    search_fields: list[str],
):
    terms = normalize_terms(
        query_text
    )

    if not terms:
        return MatchAllDocsQuery()

    outer_builder = BooleanQuery.Builder()

    if mode == "and":
        outer_occur = BooleanClause.Occur.MUST
    else:
        outer_occur = BooleanClause.Occur.SHOULD

    for term in terms:
        field_builder = BooleanQuery.Builder()

        for field in search_fields:
            field_query = build_field_query(
                term,
                field,
                analyzer,
            )

            field_builder.add(
                field_query,
                BooleanClause.Occur.SHOULD,
            )

        outer_builder.add(
            field_builder.build(),
            outer_occur,
        )

    return outer_builder.build()


def build_fuzzy_query(
    query_text: str,
    max_edits: int,
    mode: str,
    search_fields: list[str],
):
    terms = normalize_terms(
        query_text
    )

    if not terms:
        return MatchAllDocsQuery()

    outer_builder = BooleanQuery.Builder()

    if mode == "and":
        outer_occur = BooleanClause.Occur.MUST
    else:
        outer_occur = BooleanClause.Occur.SHOULD

    for term_text in terms:
        field_builder = BooleanQuery.Builder()

        for field in search_fields:
            fuzzy_query = FuzzyQuery(
                Term(
                    field,
                    term_text,
                ),
                max_edits,
            )

            field_builder.add(
                fuzzy_query,
                BooleanClause.Occur.SHOULD,
            )

        outer_builder.add(
            field_builder.build(),
            outer_occur,
        )

    return outer_builder.build()


def add_exact_filter(
    builder: BooleanQuery.Builder,
    field: str,
    value: str | None,
) -> None:
    if not value:
        return

    builder.add(
        TermQuery(
            Term(
                field,
                value,
            )
        ),
        BooleanClause.Occur.FILTER,
    )


def add_int_range_filter(
    builder: BooleanQuery.Builder,
    field: str,
    minimum: int | None,
    maximum: int | None,
) -> None:
    if minimum is None and maximum is None:
        return

    lower = (
        minimum
        if minimum is not None
        else -2147483648
    )

    upper = (
        maximum
        if maximum is not None
        else 2147483647
    )

    builder.add(
        IntPoint.newRangeQuery(
            field,
            lower,
            upper,
        ),
        BooleanClause.Occur.FILTER,
    )


def build_query(
    query_text: str,
    analyzer: StandardAnalyzer,
    mode: str = "or",
    phrase: bool = False,
    fuzzy: int | None = None,
    group: str | None = None,
    book: str | None = None,
    document_type: str | None = None,
    chapter_min: int | None = None,
    chapter_max: int | None = None,
    verse_min: int | None = None,
    verse_max: int | None = None,
    wiki_refs_min: int | None = None,
    wiki_refs_max: int | None = None,
    search_fields: list[str] | None = None,
):
    if search_fields is None:
        search_fields = SEARCH_FIELDS

    builder = BooleanQuery.Builder()

    if phrase:
        content_query = build_phrase_query(
            query_text,
            analyzer,
            search_fields,
        )

    elif fuzzy is not None:
        content_query = build_fuzzy_query(
            query_text,
            fuzzy,
            mode,
            search_fields,
        )

    else:
        content_query = build_boolean_query(
            query_text,
            analyzer,
            mode,
            search_fields,
        )

    builder.add(
        content_query,
        BooleanClause.Occur.MUST,
    )

    add_exact_filter(
        builder,
        "crawl_group",
        group,
    )

    add_exact_filter(
        builder,
        "book",
        book,
    )

    add_exact_filter(
        builder,
        "document_type",
        document_type,
    )

    add_int_range_filter(
        builder,
        "chapter",
        chapter_min,
        chapter_max,
    )

    add_int_range_filter(
        builder,
        "verse",
        verse_min,
        verse_max,
    )

    add_int_range_filter(
        builder,
        "wiki_reference_count",
        wiki_refs_min,
        wiki_refs_max,
    )

    return builder.build()


class LuceneSearchEngine:
    def __init__(
        self,
        index_path: Path = DEFAULT_INDEX,
    ) -> None:
        if lucene.getVMEnv() is None:
            lucene.initVM(
                vmargs=[
                    "-Djava.awt.headless=true",
                ]
            )

        self.directory = FSDirectory.open(
            Paths.get(
                str(index_path)
            )
        )

        self.reader = DirectoryReader.open(
            self.directory
        )

        self.searcher = IndexSearcher(
            self.reader
        )

        self.analyzer = StandardAnalyzer()

    def search(
        self,
        query_text: str,
        limit: int = 10,
        mode: str = "or",
        phrase: bool = False,
        fuzzy: int | None = None,
        group: str | None = None,
        book: str | None = None,
        document_type: str | None = None,
        chapter_min: int | None = None,
        chapter_max: int | None = None,
        verse_min: int | None = None,
        verse_max: int | None = None,
        wiki_refs_min: int | None = None,
        wiki_refs_max: int | None = None,
        search_fields: list[str] | None = None,
    ) -> list[SearchResult]:
        query = build_query(
            query_text=query_text,
            analyzer=self.analyzer,
            mode=mode,
            phrase=phrase,
            fuzzy=fuzzy,
            group=group,
            book=book,
            document_type=document_type,
            chapter_min=chapter_min,
            chapter_max=chapter_max,
            verse_min=verse_min,
            verse_max=verse_max,
            wiki_refs_min=wiki_refs_min,
            wiki_refs_max=wiki_refs_max,
            search_fields=search_fields,
        )

        top_docs = self.searcher.search(
            query,
            limit,
        )

        stored_fields = self.searcher.storedFields()

        results: list[SearchResult] = []

        for score_doc in top_docs.scoreDocs:
            document = stored_fields.document(
                score_doc.doc
            )

            results.append(
                SearchResult(
                    document_id=(
                        document.get("document_id")
                        or ""
                    ),
                    title=(
                        document.get("title")
                        or "(no title)"
                    ),
                    score=float(
                        score_doc.score
                    ),
                    crawl_group=document.get(
                        "crawl_group"
                    ),
                    url=document.get(
                        "url"
                    ),
                    preview=document.get(
                        "preview"
                    ),
                    book=document.get(
                        "book"
                    ),
                    chapter=self._get_int(
                        document,
                        "chapter",
                    ),
                    verse=self._get_int(
                        document,
                        "verse",
                    ),
                    topic=document.get(
                        "topic"
                    ),
                    place=document.get(
                        "place"
                    ),
                    wiki_title=document.get(
                        "wiki_title"
                    ),
                )
            )

        return results

    @staticmethod
    def _get_int(
        document,
        field: str,
    ) -> int | None:
        value = document.get(
            field
        )

        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def close(self) -> None:
        self.reader.close()
        self.directory.close()