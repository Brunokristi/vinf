from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

import lucene

from java.nio.file import Paths

from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document
from org.apache.lucene.document import Field
from org.apache.lucene.document import IntPoint
from org.apache.lucene.document import StoredField
from org.apache.lucene.document import StringField
from org.apache.lucene.document import TextField
from org.apache.lucene.index import IndexWriter
from org.apache.lucene.index import IndexWriterConfig
from org.apache.lucene.store import FSDirectory


DEFAULT_INPUT = Path("data/spark/search_documents")
DEFAULT_INDEX = Path("data/lucene_index")


def add_string_field(
    document: Document,
    name: str,
    value,
    stored: bool = True,
) -> None:
    if value is None:
        return

    value = str(value).strip()

    if not value:
        return

    store = Field.Store.YES if stored else Field.Store.NO
    document.add(StringField(name, value, store))


def add_text_field(
    document: Document,
    name: str,
    value,
    stored: bool = False,
) -> None:
    if value is None:
        return

    value = str(value).strip()

    if not value:
        return

    store = Field.Store.YES if stored else Field.Store.NO
    document.add(TextField(name, value, store))


def add_int_field(
    document: Document,
    name: str,
    value,
    stored: bool = False,
) -> None:
    if value is None:
        return

    try:
        number = int(value)
    except (TypeError, ValueError):
        return

    document.add(IntPoint(name, number))

    if stored:
        document.add(StoredField(name, number))


def json_list_to_text(value) -> str | None:
    if value is None:
        return None

    if isinstance(value, list):
        return " ".join(str(item) for item in value)

    if not isinstance(value, str):
        return str(value)

    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

    if isinstance(parsed, list):
        return " ".join(str(item) for item in parsed)

    return str(parsed)


def make_preview(text: str | None, limit: int = 500) -> str | None:
    if not text:
        return None

    cleaned = " ".join(text.split())

    if len(cleaned) <= limit:
        return cleaned

    return cleaned[:limit].rstrip() + "..."


def build_lucene_document(record: dict) -> Document:
    document = Document()

    add_string_field(
        document,
        "document_id",
        record.get("document_id"),
    )

    add_text_field(
        document,
        "title",
        record.get("title"),
        stored=True,
    )

    add_text_field(
        document,
        "text",
        record.get("text"),
        stored=False,
    )

    preview = make_preview(record.get("text"))

    if preview:
        document.add(
            StoredField(
                "preview",
                preview,
            )
        )

    if record.get("url"):
        document.add(
            StoredField(
                "url",
                str(record["url"]),
            )
        )

    add_string_field(
        document,
        "crawl_group",
        record.get("crawl_group"),
    )

    add_string_field(
        document,
        "document_type",
        record.get("document_type"),
    )

    add_string_field(
        document,
        "book",
        record.get("book"),
    )

    add_int_field(
        document,
        "chapter",
        record.get("chapter"),
        stored=True,
    )

    add_int_field(
        document,
        "verse",
        record.get("verse"),
        stored=True,
    )

    add_text_field(
        document,
        "topic",
        record.get("topic"),
        stored=True,
    )

    add_text_field(
        document,
        "place",
        record.get("place"),
        stored=True,
    )

    add_string_field(
        document,
        "wiki_page_id",
        record.get("wiki_page_id"),
    )

    add_text_field(
        document,
        "wiki_title",
        record.get("wiki_title"),
        stored=True,
    )

    add_text_field(
        document,
        "wiki_categories",
        json_list_to_text(
            record.get("wiki_categories")
        ),
    )

    add_text_field(
        document,
        "wiki_sections",
        json_list_to_text(
            record.get("wiki_sections")
        ),
    )

    add_text_field(
        document,
        "wiki_templates",
        json_list_to_text(
            record.get("wiki_templates")
        ),
    )

    add_text_field(
        document,
        "wiki_bold_terms",
        json_list_to_text(
            record.get("wiki_bold_terms")
        ),
    )

    add_string_field(
        document,
        "wiki_infobox_type",
        record.get("wiki_infobox_type"),
    )

    add_int_field(
        document,
        "wiki_text_length",
        record.get("wiki_text_length"),
    )

    add_int_field(
        document,
        "wiki_category_count",
        record.get("wiki_category_count"),
    )

    add_int_field(
        document,
        "wiki_section_count",
        record.get("wiki_section_count"),
    )

    add_int_field(
        document,
        "wiki_template_count",
        record.get("wiki_template_count"),
    )

    add_int_field(
        document,
        "wiki_internal_link_count",
        record.get("wiki_internal_link_count"),
    )

    add_int_field(
        document,
        "wiki_external_link_count",
        record.get("wiki_external_link_count"),
    )

    add_int_field(
        document,
        "wiki_reference_count",
        record.get("wiki_reference_count"),
    )

    return document


def iter_records(input_path: Path):
    files = sorted(input_path.glob("part-*.json"))

    if not files:
        raise FileNotFoundError(
            f"No part-*.json files found in {input_path}"
        )

    for path in files:
        print(f"Reading {path}")

        with path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            for line in handle:
                line = line.strip()

                if not line:
                    continue

                yield json.loads(line)


def build_index(
    input_path: Path,
    index_path: Path,
) -> None:
    lucene.initVM(
        vmargs=[
            "-Djava.awt.headless=true",
        ]
    )

    if index_path.exists():
        shutil.rmtree(index_path)

    index_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    directory = FSDirectory.open(
        Paths.get(str(index_path))
    )

    analyzer = StandardAnalyzer()

    config = IndexWriterConfig(analyzer)
    config.setOpenMode(
        IndexWriterConfig.OpenMode.CREATE
    )

    writer = IndexWriter(
        directory,
        config,
    )

    count = 0
    start = time.perf_counter()

    try:
        for record in iter_records(input_path):
            document = build_lucene_document(record)
            writer.addDocument(document)

            count += 1

            if count % 10_000 == 0:
                elapsed = time.perf_counter() - start

                print(
                    f"Indexed {count:,} documents "
                    f"in {elapsed:.1f} s"
                )

        writer.commit()

    finally:
        writer.close()
        directory.close()

    elapsed = time.perf_counter() - start

    print()
    print("LUCENE INDEX")
    print("============")
    print(f"Documents: {count:,}")
    print(f"Time: {elapsed:.2f} s")
    print(f"Index: {index_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Build PyLucene index."
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
    )

    parser.add_argument(
        "--index",
        type=Path,
        default=DEFAULT_INDEX,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    build_index(
        args.input,
        args.index,
    )


if __name__ == "__main__":
    main()
