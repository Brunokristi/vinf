from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENTS_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "documents.jsonl"
)

BOOK_MAPPING_FILE = (
    PROJECT_ROOT
    / "data"
    / "mappings"
    / "bible_books.tsv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "spark"
    / "biblehub_entities"
)


def create_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("BiblicalSearch-BibleHubEntities")
        .master("local[8]")
        .config("spark.sql.shuffle.partitions", "32")
        .getOrCreate()
    )


def normalize_join_key(column):
    return F.lower(
        F.trim(
            F.regexp_replace(
                column,
                r"\s+",
                " ",
            )
        )
    )


def build_places(documents):
    return (
        documents
        .filter(F.col("crawl_group") == "atlas")
        .filter(F.col("place").isNotNull())
        .filter(F.length(F.trim(F.col("place"))) > 0)
        .select(
            "document_id",
            "crawl_group",
            "url",
            "title",
            F.col("place").alias("source_entity"),
        )
        .withColumn(
            "entity_name",
            F.col("source_entity"),
        )
        .withColumn(
            "entity_type",
            F.lit("place"),
        )
        .withColumn(
            "join_key",
            normalize_join_key(F.col("entity_name")),
        )
    )


def build_naves_entities(documents):
    return (
        documents
        .filter(F.col("crawl_group") == "naves")
        .filter(F.col("topic").isNotNull())
        .filter(F.length(F.trim(F.col("topic"))) > 0)
        .select(
            "document_id",
            "crawl_group",
            "url",
            "title",
            F.col("topic").alias("source_entity"),
        )
        .withColumn(
            "entity_name",
            F.trim(
                F.regexp_extract(
                    F.col("source_entity"),
                    r"^([^:]+)",
                    1,
                )
            ),
        )
        .filter(F.length(F.col("entity_name")) > 0)
        .withColumn(
            "entity_type",
            F.lit("naves_entity"),
        )
        .withColumn(
            "join_key",
            normalize_join_key(F.col("entity_name")),
        )
    )


def build_books(documents, spark):
    mapping = (
        spark.read
        .option("header", True)
        .option("sep", "\t")
        .csv(str(BOOK_MAPPING_FILE))
    )

    bible_books = (
        documents
        .filter(F.col("crawl_group") == "bible")
        .filter(F.col("book").isNotNull())
        .filter(F.length(F.trim(F.col("book"))) > 0)
        .select(
            "document_id",
            "crawl_group",
            "url",
            "title",
            F.col("book").alias("source_entity"),
        )
    )

    return (
        bible_books
        .join(
            mapping,
            bible_books["source_entity"] == mapping["bible_book"],
            "left",
        )
        .withColumn(
            "entity_name",
            F.coalesce(
                F.col("wiki_title"),
                F.col("source_entity"),
            ),
        )
        .withColumn(
            "entity_type",
            F.lit("book"),
        )
        .withColumn(
            "join_key",
            normalize_join_key(F.col("entity_name")),
        )
        .select(
            "document_id",
            "crawl_group",
            "url",
            "title",
            "source_entity",
            "entity_name",
            "entity_type",
            "join_key",
        )
    )


def main() -> None:
    spark = create_spark()
    spark.sparkContext.setLogLevel("WARN")

    documents = (
        spark.read
        .json(str(DOCUMENTS_FILE))
        .select(
            "document_id",
            "crawl_group",
            "book",
            "place",
            "topic",
            "url",
            "title",
        )
    )

    places = build_places(documents)
    naves_entities = build_naves_entities(documents)
    books = build_books(documents, spark)

    entities = (
        places
        .unionByName(
            naves_entities,
            allowMissingColumns=True,
        )
        .unionByName(
            books,
            allowMissingColumns=True,
        )
    )

    print(f"Entity records: {entities.count()}")

    print("Records by entity type:")

    (
        entities
        .groupBy("entity_type")
        .count()
        .orderBy("entity_type")
        .show(truncate=False)
    )

    unique_entities = (
        entities
        .select(
            "entity_type",
            "entity_name",
            "join_key",
        )
        .dropDuplicates([
            "entity_type",
            "join_key",
        ])
    )

    print(f"Unique entities: {unique_entities.count()}")

    print("Unique entities by type:")

    (
        unique_entities
        .groupBy("entity_type")
        .count()
        .orderBy("entity_type")
        .show(truncate=False)
    )

    for entity_type in (
        "place",
        "naves_entity",
        "book",
    ):
        print(f"\nExamples: {entity_type}")

        (
            unique_entities
            .filter(F.col("entity_type") == entity_type)
            .orderBy("join_key")
            .show(20, truncate=False)
        )

    (
        entities
        .write
        .mode("overwrite")
        .option("header", True)
        .option("sep", "\t")
        .csv(str(OUTPUT_DIR))
    )

    spark.stop()


if __name__ == "__main__":
    main()