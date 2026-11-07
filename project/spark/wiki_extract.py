from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from pyspark.sql import Row, SparkSession
from pyspark.sql import functions as F

from .wiki_regex import parse_page


PROJECT_ROOT = Path(__file__).resolve().parent.parent

WIKI_DIR = PROJECT_ROOT / "data" / "wiki"

INPUT_GLOB = str(
    WIKI_DIR
    / "enwiki-2026-10-01-*.xml.bz2"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "spark"
    / "wikipedia_pages"
)


def create_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("BiblicalSearch-WikipediaExtract")
        .master("local[4]")
        .config("spark.sql.shuffle.partitions", "16")
        .getOrCreate()
    )


def page_records(
    records: Iterator[tuple[object, object]],
) -> Iterator[Row]:
    for _, raw_value in records:
        value = str(raw_value)

        page_start = value.find("<page>")

        if page_start < 0:
            continue

        page_xml = value[page_start:] + "</page>"

        page = parse_page(page_xml)

        if page is None:
            continue

        if page["namespace"] != 0:
            continue

        yield Row(
            page_id=int(page["page_id"]),
            title=str(page["title"]),
            join_key=str(page["join_key"]),
            namespace=int(page["namespace"]),
            redirect=page["redirect"],

            categories=json.dumps(
                page["categories"],
                ensure_ascii=False,
            ),

            sections=json.dumps(
                page["sections"],
                ensure_ascii=False,
            ),

            templates=json.dumps(
                page["templates"],
                ensure_ascii=False,
            ),

            infobox_type=page["infobox_type"],

            bold_terms=json.dumps(
                page["bold_terms"][:20],
                ensure_ascii=False,
            ),

            category_count=len(
                page["categories"]
            ),

            section_count=len(
                page["sections"]
            ),

            template_count=len(
                page["templates"]
            ),

            internal_link_count=len(
                page["internal_links"]
            ),

            external_link_count=len(
                page["external_links"]
            ),

            reference_count=int(
                page["reference_count"]
            ),

            text_length=int(
                page["text_length"]
            ),
        )


def main() -> None:
    spark = create_spark()

    spark.sparkContext.setLogLevel("WARN")

    print()
    print("Wikipedia extraction")
    print("--------------------")
    print(f"Input:  {INPUT_GLOB}")
    print(f"Output: {OUTPUT_DIR}")
    print()

    records = spark.sparkContext.newAPIHadoopFile(
        INPUT_GLOB,
        "org.apache.hadoop.mapreduce.lib.input.TextInputFormat",
        "org.apache.hadoop.io.LongWritable",
        "org.apache.hadoop.io.Text",
        conf={
            "textinputformat.record.delimiter": "</page>",
        },
    )

    print(
        "Input partitions:",
        records.getNumPartitions(),
    )

    pages_rdd = records.mapPartitions(
        page_records,
    )

    pages = spark.createDataFrame(
        pages_rdd,
    )

    print()
    print("Writing extracted Wikipedia pages...")

    (
        pages
        .write
        .mode("overwrite")
        .option("header", True)
        .option("sep", "\t")
        .option("quote", '"')
        .option("escape", '"')
        .csv(str(OUTPUT_DIR))
    )

    print(
        "Wikipedia extraction written successfully."
    )
    print()

    saved_pages = (
        spark.read
        .option("header", True)
        .option("sep", "\t")
        .option("inferSchema", True)
        .csv(str(OUTPUT_DIR))
    )

    total_pages = saved_pages.count()

    redirect_count = (
        saved_pages
        .filter(
            saved_pages["redirect"].isNotNull()
        )
        .count()
    )

    article_count = (
        total_pages
        - redirect_count
    )

    print("Wikipedia statistics")
    print("--------------------")

    print(
        f"Parsed namespace-0 pages: "
        f"{total_pages:,}"
    )

    print(
        f"Articles: "
        f"{article_count:,}"
    )

    print(
        f"Redirects: "
        f"{redirect_count:,}"
    )

    content_stats = (
        saved_pages
        .filter(
            F.col("redirect").isNull()
        )
        .agg(
            F.avg(
                "text_length"
            ).alias(
                "avg_text_length"
            ),
            F.avg(
                "category_count"
            ).alias(
                "avg_categories"
            ),
            F.avg(
                "section_count"
            ).alias(
                "avg_sections"
            ),
            F.avg(
                "template_count"
            ).alias(
                "avg_templates"
            ),
            F.avg(
                "internal_link_count"
            ).alias(
                "avg_internal_links"
            ),
            F.avg(
                "external_link_count"
            ).alias(
                "avg_external_links"
            ),
            F.avg(
                "reference_count"
            ).alias(
                "avg_references"
            ),
        )
        .first()
    )

    print()
    print("Average article attributes")
    print("--------------------------")

    print(
        "Average text length: "
        f"{content_stats['avg_text_length']:.2f}"
    )

    print(
        "Average categories: "
        f"{content_stats['avg_categories']:.2f}"
    )

    print(
        "Average sections: "
        f"{content_stats['avg_sections']:.2f}"
    )

    print(
        "Average templates: "
        f"{content_stats['avg_templates']:.2f}"
    )

    print(
        "Average internal links: "
        f"{content_stats['avg_internal_links']:.2f}"
    )

    print(
        "Average external links: "
        f"{content_stats['avg_external_links']:.2f}"
    )

    print(
        "Average references: "
        f"{content_stats['avg_references']:.2f}"
    )

    print()
    print("Examples:")

    (
        saved_pages
        .filter(
            F.col("redirect").isNull()
        )
        .select(
            "page_id",
            "title",
            "text_length",
            "category_count",
            "section_count",
            "template_count",
            "internal_link_count",
            "external_link_count",
            "reference_count",
            "infobox_type",
        )
        .orderBy(
            "page_id",
        )
        .show(
            20,
            truncate=False,
        )
    )

    print()
    print("Examples with extracted structure:")

    (
        saved_pages
        .filter(
            F.col("redirect").isNull()
        )
        .filter(
            F.col("section_count") > 0
        )
        .select(
            "title",
            "sections",
            "categories",
            "templates",
            "infobox_type",
            "bold_terms",
        )
        .orderBy(
            "page_id",
        )
        .show(
            10,
            truncate=120,
        )
    )

    print()
    print("Largest pages by text length:")

    (
        saved_pages
        .filter(
            F.col("redirect").isNull()
        )
        .select(
            "page_id",
            "title",
            "text_length",
            "category_count",
            "section_count",
            "template_count",
            "internal_link_count",
            "external_link_count",
            "reference_count",
        )
        .orderBy(
            F.col(
                "text_length"
            ).desc(),
        )
        .show(
            10,
            truncate=False,
        )
    )

    print()
    print("Most referenced pages:")

    (
        saved_pages
        .filter(
            F.col("redirect").isNull()
        )
        .select(
            "page_id",
            "title",
            "reference_count",
            "section_count",
            "external_link_count",
        )
        .orderBy(
            F.col(
                "reference_count"
            ).desc(),
        )
        .show(
            10,
            truncate=False,
        )
    )

    print()
    print("Done.")

    spark.stop()


if __name__ == "__main__":
    main()