from __future__ import annotations

from pathlib import Path

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


PROJECT_ROOT = Path(__file__).resolve().parent.parent

BIBLEHUB_ENTITIES_DIR = (
    PROJECT_ROOT
    / "data"
    / "spark"
    / "biblehub_entities"
)

WIKIPEDIA_PAGES_DIR = (
    PROJECT_ROOT
    / "data"
    / "spark"
    / "wikipedia_pages"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "spark"
    / "biblehub_wikipedia_join"
)


def create_spark() -> SparkSession:
    return (
        SparkSession.builder
        .appName("BiblicalSearch-WikipediaJoin")
        .master("local[4]")
        .config("spark.sql.shuffle.partitions", "32")
        .getOrCreate()
    )


def normalize_join_key(
    column: F.Column,
) -> F.Column:
    value = F.lower(
        F.trim(
            F.regexp_replace(
                column,
                "_",
                " ",
            )
        )
    )

    return F.regexp_replace(
        value,
        r"\s+",
        " ",
    )


def load_biblehub_entities(
    spark: SparkSession,
) -> DataFrame:
    entities = (
        spark.read
        .option("header", True)
        .option("sep", "\t")
        .csv(str(BIBLEHUB_ENTITIES_DIR))
    )

    return (
        entities
        .select(
            "entity_type",
            "entity_name",
            "join_key",
        )
        .filter(
            F.col("join_key").isNotNull()
        )
        .filter(
            F.length(
                F.col("join_key")
            ) > 0
        )
        .dropDuplicates(
            [
                "entity_type",
                "join_key",
            ]
        )
    )


def load_wikipedia_pages(
    spark: SparkSession,
) -> DataFrame:
    pages = (
        spark.read
        .option("header", True)
        .option("sep", "\t")
        .option("inferSchema", True)
        .csv(str(WIKIPEDIA_PAGES_DIR))
    )

    return (
        pages
        .select(
            F.col("page_id").cast("long"),
            "title",
            "join_key",
            "redirect",

            "categories",
            "sections",
            "templates",
            "infobox_type",
            "bold_terms",

            F.col(
                "text_length"
            ).cast(
                "long"
            ),

            F.col(
                "category_count"
            ).cast(
                "long"
            ),

            F.col(
                "section_count"
            ).cast(
                "long"
            ),

            F.col(
                "template_count"
            ).cast(
                "long"
            ),

            F.col(
                "internal_link_count"
            ).cast(
                "long"
            ),

            F.col(
                "external_link_count"
            ).cast(
                "long"
            ),

            F.col(
                "reference_count"
            ).cast(
                "long"
            ),
        )
        .filter(
            F.col("join_key").isNotNull()
        )
    )


def build_title_lookup(
    wikipedia: DataFrame,
) -> DataFrame:
    return (
        wikipedia
        .select(
            F.col(
                "join_key"
            ).alias(
                "wiki_join_key"
            ),

            F.col(
                "page_id"
            ).alias(
                "wiki_page_id"
            ),

            F.col(
                "title"
            ).alias(
                "wiki_title"
            ),

            F.col(
                "redirect"
            ).alias(
                "wiki_redirect"
            ),

            F.col(
                "categories"
            ).alias(
                "wiki_categories"
            ),

            F.col(
                "sections"
            ).alias(
                "wiki_sections"
            ),

            F.col(
                "templates"
            ).alias(
                "wiki_templates"
            ),

            F.col(
                "infobox_type"
            ).alias(
                "wiki_infobox_type"
            ),

            F.col(
                "bold_terms"
            ).alias(
                "wiki_bold_terms"
            ),

            F.col(
                "text_length"
            ).alias(
                "wiki_text_length"
            ),

            F.col(
                "category_count"
            ).alias(
                "wiki_category_count"
            ),

            F.col(
                "section_count"
            ).alias(
                "wiki_section_count"
            ),

            F.col(
                "template_count"
            ).alias(
                "wiki_template_count"
            ),

            F.col(
                "internal_link_count"
            ).alias(
                "wiki_internal_link_count"
            ),

            F.col(
                "external_link_count"
            ).alias(
                "wiki_external_link_count"
            ),

            F.col(
                "reference_count"
            ).alias(
                "wiki_reference_count"
            ),
        )
        .dropDuplicates(
            [
                "wiki_join_key",
            ]
        )
    )


def build_article_lookup(
    wikipedia: DataFrame,
) -> DataFrame:
    return (
        wikipedia
        .filter(
            F.col("redirect").isNull()
        )
        .select(
            F.col(
                "join_key"
            ).alias(
                "article_join_key"
            ),

            F.col(
                "page_id"
            ).alias(
                "article_page_id"
            ),

            F.col(
                "title"
            ).alias(
                "article_title"
            ),

            F.col(
                "categories"
            ).alias(
                "article_categories"
            ),

            F.col(
                "sections"
            ).alias(
                "article_sections"
            ),

            F.col(
                "templates"
            ).alias(
                "article_templates"
            ),

            F.col(
                "infobox_type"
            ).alias(
                "article_infobox_type"
            ),

            F.col(
                "bold_terms"
            ).alias(
                "article_bold_terms"
            ),

            F.col(
                "text_length"
            ).alias(
                "article_text_length"
            ),

            F.col(
                "category_count"
            ).alias(
                "article_category_count"
            ),

            F.col(
                "section_count"
            ).alias(
                "article_section_count"
            ),

            F.col(
                "template_count"
            ).alias(
                "article_template_count"
            ),

            F.col(
                "internal_link_count"
            ).alias(
                "article_internal_link_count"
            ),

            F.col(
                "external_link_count"
            ).alias(
                "article_external_link_count"
            ),

            F.col(
                "reference_count"
            ).alias(
                "article_reference_count"
            ),
        )
        .dropDuplicates(
            [
                "article_join_key",
            ]
        )
    )


def resolved_value(
    redirect_column: str,
    article_column: str,
    direct_column: str,
) -> F.Column:
    return (
        F.when(
            F.col(
                redirect_column
            ).isNotNull()
            & F.col(
                article_column
            ).isNotNull(),
            F.col(
                article_column
            ),
        )
        .otherwise(
            F.col(
                direct_column
            )
        )
    )


def join_entities_with_wikipedia(
    entities: DataFrame,
    wikipedia: DataFrame,
) -> DataFrame:
    title_lookup = build_title_lookup(
        wikipedia,
    )

    article_lookup = build_article_lookup(
        wikipedia,
    )

    direct = (
        entities.alias("e")
        .join(
            title_lookup.alias("w"),
            F.col("e.join_key")
            == F.col("w.wiki_join_key"),
            "left",
        )
    )

    direct = (
        direct
        .withColumn(
            "redirect_join_key",
            F.when(
                F.col(
                    "w.wiki_redirect"
                ).isNotNull(),
                normalize_join_key(
                    F.col(
                        "w.wiki_redirect"
                    )
                ),
            ),
        )
    )

    joined = (
        direct.alias("d")
        .join(
            article_lookup.alias("a"),
            F.col(
                "d.redirect_join_key"
            )
            == F.col(
                "a.article_join_key"
            ),
            "left",
        )
    )

    return (
        joined
        .select(
            F.col(
                "d.entity_type"
            ).alias(
                "entity_type"
            ),

            F.col(
                "d.entity_name"
            ).alias(
                "entity_name"
            ),

            F.col(
                "d.join_key"
            ).alias(
                "join_key"
            ),

            F.col(
                "d.wiki_page_id"
            ).alias(
                "matched_page_id"
            ),

            F.col(
                "d.wiki_title"
            ).alias(
                "matched_title"
            ),

            F.col(
                "d.wiki_redirect"
            ).alias(
                "redirect_title"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_page_id",
                "d.wiki_page_id",
            ).alias(
                "final_page_id"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_title",
                "d.wiki_title",
            ).alias(
                "final_title"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_categories",
                "d.wiki_categories",
            ).alias(
                "categories"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_sections",
                "d.wiki_sections",
            ).alias(
                "sections"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_templates",
                "d.wiki_templates",
            ).alias(
                "templates"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_infobox_type",
                "d.wiki_infobox_type",
            ).alias(
                "infobox_type"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_bold_terms",
                "d.wiki_bold_terms",
            ).alias(
                "bold_terms"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_text_length",
                "d.wiki_text_length",
            ).alias(
                "text_length"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_category_count",
                "d.wiki_category_count",
            ).alias(
                "category_count"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_section_count",
                "d.wiki_section_count",
            ).alias(
                "section_count"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_template_count",
                "d.wiki_template_count",
            ).alias(
                "template_count"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_internal_link_count",
                "d.wiki_internal_link_count",
            ).alias(
                "internal_link_count"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_external_link_count",
                "d.wiki_external_link_count",
            ).alias(
                "external_link_count"
            ),

            resolved_value(
                "d.wiki_redirect",
                "a.article_reference_count",
                "d.wiki_reference_count",
            ).alias(
                "reference_count"
            ),

            F.when(
                F.col(
                    "d.wiki_page_id"
                ).isNotNull(),
                F.lit(True),
            )
            .otherwise(
                F.lit(False),
            )
            .alias(
                "matched"
            ),

            F.when(
                F.col(
                    "d.wiki_redirect"
                ).isNotNull()
                & F.col(
                    "a.article_page_id"
                ).isNotNull(),
                F.lit(True),
            )
            .otherwise(
                F.lit(False),
            )
            .alias(
                "redirect_resolved"
            ),
        )
    )


def print_statistics(
    joined: DataFrame,
) -> None:
    statistics = (
        joined
        .groupBy(
            "entity_type",
        )
        .agg(
            F.count(
                "*"
            ).alias(
                "total"
            ),

            F.sum(
                F.when(
                    F.col("matched"),
                    1,
                ).otherwise(0)
            ).alias(
                "matched"
            ),

            F.sum(
                F.when(
                    ~F.col("matched"),
                    1,
                ).otherwise(0)
            ).alias(
                "unmatched"
            ),

            F.sum(
                F.when(
                    F.col(
                        "redirect_resolved"
                    ),
                    1,
                ).otherwise(0)
            ).alias(
                "redirects_resolved"
            ),
        )
        .withColumn(
            "match_rate_percent",
            F.round(
                (
                    F.col("matched")
                    / F.col("total")
                )
                * 100,
                2,
            ),
        )
        .orderBy(
            "entity_type",
        )
    )

    print()
    print("Match statistics")
    print("----------------")

    statistics.show(
        truncate=False,
    )

    totals = (
        joined
        .agg(
            F.count(
                "*"
            ).alias(
                "total"
            ),

            F.sum(
                F.when(
                    F.col("matched"),
                    1,
                ).otherwise(0)
            ).alias(
                "matched"
            ),

            F.sum(
                F.when(
                    ~F.col("matched"),
                    1,
                ).otherwise(0)
            ).alias(
                "unmatched"
            ),

            F.countDistinct(
                F.when(
                    F.col("matched"),
                    F.col(
                        "final_page_id"
                    ),
                )
            ).alias(
                "unique_wikipedia_pages"
            ),
        )
        .first()
    )

    total = int(
        totals["total"]
    )

    matched = int(
        totals["matched"]
    )

    unmatched = int(
        totals["unmatched"]
    )

    unique_wikipedia_pages = int(
        totals[
            "unique_wikipedia_pages"
        ]
    )

    match_rate = (
        matched / total * 100
        if total
        else 0.0
    )

    print()
    print("Overall")
    print("-------")

    print(
        f"Entities: "
        f"{total:,}"
    )

    print(
        f"Matched: "
        f"{matched:,}"
    )

    print(
        f"Unmatched: "
        f"{unmatched:,}"
    )

    print(
        f"Match rate: "
        f"{match_rate:.2f}%"
    )

    print(
        "Unique Wikipedia pages joined: "
        f"{unique_wikipedia_pages:,}"
    )


def print_wikipedia_attribute_statistics(
    joined: DataFrame,
) -> None:
    stats = (
        joined
        .filter(
            F.col("matched")
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

            F.sum(
                F.when(
                    F.col(
                        "infobox_type"
                    ).isNotNull(),
                    1,
                ).otherwise(0)
            ).alias(
                "with_infobox"
            ),
        )
        .first()
    )

    print()
    print("Joined Wikipedia attributes")
    print("----------------------------")

    print(
        "Average text length: "
        f"{stats['avg_text_length']:.2f}"
    )

    print(
        "Average categories: "
        f"{stats['avg_categories']:.2f}"
    )

    print(
        "Average sections: "
        f"{stats['avg_sections']:.2f}"
    )

    print(
        "Average templates: "
        f"{stats['avg_templates']:.2f}"
    )

    print(
        "Average internal links: "
        f"{stats['avg_internal_links']:.2f}"
    )

    print(
        "Average external links: "
        f"{stats['avg_external_links']:.2f}"
    )

    print(
        "Average references: "
        f"{stats['avg_references']:.2f}"
    )

    print(
        "Matched entities with infobox: "
        f"{int(stats['with_infobox']):,}"
    )


def print_examples(
    joined: DataFrame,
) -> None:
    print()
    print("Matched examples")
    print("----------------")

    (
        joined
        .filter(
            F.col("matched")
        )
        .select(
            "entity_type",
            "entity_name",
            "final_title",
            "redirect_title",
            "category_count",
            "section_count",
            "template_count",
            "internal_link_count",
            "external_link_count",
            "reference_count",
            "infobox_type",
        )
        .orderBy(
            "entity_type",
            "entity_name",
        )
        .show(
            30,
            truncate=False,
        )
    )

    print()
    print("Matched examples with Wiki structure")
    print("------------------------------------")

    (
        joined
        .filter(
            F.col("matched")
        )
        .filter(
            F.col("section_count") > 0
        )
        .select(
            "entity_type",
            "entity_name",
            "final_title",
            "categories",
            "sections",
            "infobox_type",
            "bold_terms",
        )
        .orderBy(
            "entity_type",
            "entity_name",
        )
        .show(
            15,
            truncate=120,
        )
    )

    print()
    print("Unmatched examples")
    print("------------------")

    (
        joined
        .filter(
            ~F.col("matched")
        )
        .select(
            "entity_type",
            "entity_name",
            "join_key",
        )
        .orderBy(
            "entity_type",
            "entity_name",
        )
        .show(
            30,
            truncate=False,
        )
    )


def main() -> None:
    spark = create_spark()

    spark.sparkContext.setLogLevel(
        "WARN"
    )

    print()
    print("BibleHub <-> Wikipedia join")
    print("---------------------------")

    print(
        f"BibleHub:  "
        f"{BIBLEHUB_ENTITIES_DIR}"
    )

    print(
        f"Wikipedia: "
        f"{WIKIPEDIA_PAGES_DIR}"
    )

    print(
        f"Output:    "
        f"{OUTPUT_DIR}"
    )

    entities = load_biblehub_entities(
        spark,
    )

    wikipedia = load_wikipedia_pages(
        spark,
    )

    print()

    print(
        "Unique BibleHub entities:",
        entities.count(),
    )

    print(
        "Wikipedia namespace-0 pages:",
        wikipedia.count(),
    )

    joined = join_entities_with_wikipedia(
        entities,
        wikipedia,
    )

    print_statistics(
        joined,
    )

    print_wikipedia_attribute_statistics(
        joined,
    )

    print_examples(
        joined,
    )

    print()
    print("Writing joined dataset...")

    (
        joined
        .write
        .mode("overwrite")
        .option("header", True)
        .option("sep", "\t")
        .option("quote", '"')
        .option("escape", '"')
        .csv(str(OUTPUT_DIR))
    )

    print(
        "Joined dataset written successfully."
    )

    spark.stop()


if __name__ == "__main__":
    main()