from __future__ import annotations

from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "documents.jsonl"
OUTPUT_DIR = PROJECT_ROOT / "data" / "spark" / "biblehub_stats"


def main() -> None:
    spark = (
        SparkSession.builder
        .appName("BiblicalSearch-BibleHubStats")
        .master("local[*]")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    documents = spark.read.json(str(INPUT_FILE))

    print("Schema:")
    documents.printSchema()

    total_documents = documents.count()

    print(f"Total documents: {total_documents}")

    group_stats = (
        documents
        .groupBy("crawl_group")
        .agg(
            F.count("*").alias("document_count"),
            F.sum("word_count").alias("total_words"),
            F.avg("word_count").alias("average_words"),
        )
        .orderBy("crawl_group")
    )

    group_stats.show(truncate=False)

    (
        group_stats
        .write
        .mode("overwrite")
        .option("header", True)
        .option("sep", "\t")
        .csv(str(OUTPUT_DIR))
    )

    spark.stop()


if __name__ == "__main__":
    main()