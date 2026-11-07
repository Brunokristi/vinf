from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StringType


DOCUMENTS_PATH = "data/processed/documents.jsonl"
BOOK_MAPPING_PATH = "data/mappings/bible_books.tsv"
WIKI_JOIN_PATH = "data/spark/biblehub_wikipedia_join"

OUTPUT_PATH = "data/spark/search_documents"


def normalize_join_key(column):
    return F.lower(
        F.trim(
            F.regexp_replace(
                F.regexp_replace(column, "_", " "),
                r"\s+",
                " ",
            )
        )
    )


def optional_column(df: DataFrame, name: str, data_type: str = "string"):
    if name in df.columns:
        return F.col(name)

    return F.lit(None).cast(data_type)


def load_documents(spark: SparkSession) -> DataFrame:
    documents = spark.read.json(DOCUMENTS_PATH)

    return documents.select(
        optional_column(documents, "document_id").alias("document_id"),
        optional_column(documents, "title").alias("title"),
        optional_column(documents, "text").alias("text"),
        optional_column(documents, "url").alias("url"),
        optional_column(documents, "crawl_group").alias("crawl_group"),
        optional_column(documents, "document_type").alias("document_type"),
        optional_column(documents, "book").alias("book"),
        optional_column(documents, "chapter", "int").alias("chapter"),
        optional_column(documents, "verse", "int").alias("verse"),
        optional_column(documents, "topic").alias("topic"),
        optional_column(documents, "place").alias("place"),
    )


def load_book_mapping(spark: SparkSession) -> DataFrame:
    mapping = (
        spark.read
        .option("header", True)
        .option("sep", "\t")
        .csv(BOOK_MAPPING_PATH)
    )

    return (
        mapping
        .select(
            F.col("bible_book").alias("mapping_book"),
            F.col("wiki_title").alias("mapping_wiki_title"),
        )
        .withColumn(
            "mapping_join_key",
            normalize_join_key(F.col("mapping_wiki_title")),
        )
    )


def load_wikipedia_join(spark: SparkSession) -> DataFrame:
    wiki = (
        spark.read
        .option("header", True)
        .option("sep", "\t")
        .csv(WIKI_JOIN_PATH)
    )

    return wiki.select(
        F.col("entity_type").alias("wiki_entity_type"),
        F.col("join_key").alias("wiki_join_key"),
        F.col("matched").alias("wiki_matched"),
        F.col("final_page_id").alias("wiki_page_id"),
        F.col("final_title").alias("wiki_title"),
        F.col("categories").alias("wiki_categories"),
        F.col("sections").alias("wiki_sections"),
        F.col("templates").alias("wiki_templates"),
        F.col("infobox_type").alias("wiki_infobox_type"),
        F.col("bold_terms").alias("wiki_bold_terms"),
        F.col("text_length").cast("int").alias("wiki_text_length"),
        F.col("category_count").cast("int").alias("wiki_category_count"),
        F.col("section_count").cast("int").alias("wiki_section_count"),
        F.col("template_count").cast("int").alias("wiki_template_count"),
        F.col("internal_link_count").cast("int").alias(
            "wiki_internal_link_count"
        ),
        F.col("external_link_count").cast("int").alias(
            "wiki_external_link_count"
        ),
        F.col("reference_count").cast("int").alias(
            "wiki_reference_count"
        ),
    )


def add_entity_keys(
    documents: DataFrame,
    book_mapping: DataFrame,
) -> DataFrame:
    documents = documents.join(
        book_mapping,
        documents.book == book_mapping.mapping_book,
        "left",
    )

    naves_entity = F.regexp_extract(
        F.col("topic"),
        r"^([^:]+)",
        1,
    )

    return (
        documents
        .withColumn(
            "entity_type",
            F.when(
                F.col("crawl_group") == "bible",
                F.lit("book"),
            )
            .when(
                F.col("crawl_group") == "naves",
                F.lit("naves_entity"),
            )
            .when(
                F.col("crawl_group") == "atlas",
                F.lit("place"),
            ),
        )
        .withColumn(
            "entity_join_key",
            F.when(
                F.col("crawl_group") == "bible",
                F.col("mapping_join_key"),
            )
            .when(
                F.col("crawl_group") == "naves",
                normalize_join_key(naves_entity),
            )
            .when(
                F.col("crawl_group") == "atlas",
                normalize_join_key(F.col("place")),
            ),
        )
        .drop(
            "mapping_book",
            "mapping_wiki_title",
            "mapping_join_key",
        )
    )


def enrich_with_wikipedia(
    documents: DataFrame,
    wiki: DataFrame,
) -> DataFrame:
    return (
        documents
        .join(
            wiki,
            (
                documents.entity_type == wiki.wiki_entity_type
            )
            & (
                documents.entity_join_key == wiki.wiki_join_key
            ),
            "left",
        )
        .drop(
            "wiki_entity_type",
            "wiki_join_key",
        )
    )


def prepare_output(documents: DataFrame) -> DataFrame:
    return documents.select(
        "document_id",
        "title",
        "text",
        "url",
        "crawl_group",
        "document_type",
        "book",
        "chapter",
        "verse",
        "topic",
        "place",
        "wiki_matched",
        "wiki_page_id",
        "wiki_title",
        "wiki_categories",
        "wiki_sections",
        "wiki_templates",
        "wiki_infobox_type",
        "wiki_bold_terms",
        "wiki_text_length",
        "wiki_category_count",
        "wiki_section_count",
        "wiki_template_count",
        "wiki_internal_link_count",
        "wiki_external_link_count",
        "wiki_reference_count",
    )


def print_stats(documents: DataFrame) -> None:
    total = documents.count()

    print()
    print("SEARCH DOCUMENT DATASET")
    print("=======================")
    print(f"Documents: {total:,}")
    print()

    print("BY CRAWL GROUP")
    documents.groupBy("crawl_group").count().orderBy(
        "crawl_group"
    ).show(
        truncate=False
    )

    enriched = documents.filter(
        F.col("wiki_title").isNotNull()
    ).count()

    print(f"Wikipedia enriched documents: {enriched:,}")
    print(
        f"Without Wikipedia enrichment: "
        f"{total - enriched:,}"
    )

    print()
    print("WIKIPEDIA ENRICHMENT BY GROUP")

    (
        documents
        .groupBy("crawl_group")
        .agg(
            F.count("*").alias("documents"),
            F.sum(
                F.when(
                    F.col("wiki_title").isNotNull(),
                    1,
                ).otherwise(0)
            ).alias("wiki_enriched"),
        )
        .withColumn(
            "wiki_rate",
            F.round(
                F.col("wiki_enriched")
                / F.col("documents")
                * 100,
                2,
            ),
        )
        .orderBy("crawl_group")
        .show(truncate=False)
    )

    print()
    print("EXAMPLES")

    (
        documents
        .filter(F.col("wiki_title").isNotNull())
        .select(
            "document_id",
            "crawl_group",
            "title",
            "book",
            "topic",
            "place",
            "wiki_title",
        )
        .show(20, truncate=70)
    )


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("Build Lucene Search Documents")
        .master("local[4]")
        .config("spark.sql.shuffle.partitions", "16")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    documents = load_documents(spark)
    book_mapping = load_book_mapping(spark)
    wiki = load_wikipedia_join(spark)

    documents = add_entity_keys(
        documents,
        book_mapping,
    )

    documents = enrich_with_wikipedia(
        documents,
        wiki,
    )

    documents = prepare_output(documents)

    print_stats(documents)

    (
        documents
        .write
        .mode("overwrite")
        .json(OUTPUT_PATH)
    )

    print()
    print(f"Written to: {OUTPUT_PATH}")

    spark.stop()


if __name__ == "__main__":
    main()