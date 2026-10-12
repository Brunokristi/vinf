from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Iterable

from .idf import SUPPORTED_IDF_METHODS, idf, log_tf
from .tokenizer import tokenize


INDEX_VERSION = "0.1"


@dataclass(frozen=True)
class IndexPaths:
    project_root: Path

    @property
    def source_documents(self) -> Path:
        return self.project_root / "data" / "processed" / "documents.jsonl"

    @property
    def index_dir(self) -> Path:
        return self.project_root / "data" / "index"

    @property
    def index_file(self) -> Path:
        return self.index_dir / "index.jsonl"

    @property
    def catalog_file(self) -> Path:
        return self.index_dir / "documents.jsonl"

    @property
    def stats_file(self) -> Path:
        return self.index_dir / "stats.json"

    @property
    def vocabulary_file(self) -> Path:
        return self.index_dir / "vocabulary.txt"


class InvertedIndexBuilder:
    def __init__(self, project_root: Path):
        self.paths = IndexPaths(project_root.resolve())
        self.paths.index_dir.mkdir(parents=True, exist_ok=True)

    def _load_documents(self) -> Iterable[dict]:
        if not self.paths.source_documents.exists():
            raise FileNotFoundError(
                f"Extracted documents not found: {self.paths.source_documents}. "
                "Run `python -m extractor` first."
            )

        with self.paths.source_documents.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    document = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSON on line {line_number} of {self.paths.source_documents}"
                    ) from exc
                if document.get("valid") is False:
                    continue
                yield document

    @staticmethod
    def _catalog_record(document: dict, doc_number: int, token_count: int) -> dict:
        record = {
            "doc_number": doc_number,
            "document_id": document["document_id"],
            "url": document["url"],
            "title": document.get("title") or document["url"],
            "document_type": document.get("document_type"),
            "source_collection": document.get("source_collection"),
            "token_count": token_count,
            "preview": " ".join(str(document.get("text") or "").split())[:320],
        }

        for field in (
            "book",
            "chapter",
            "verse",
            "reference",
            "topic",
            "place",
        ):
            if document.get(field) is not None:
                record[field] = document[field]

        return record

    def build(self, limit: int | None = None) -> dict:
        # postings[term][doc_number] = raw term count in that document
        postings: dict[str, dict[int, int]] = defaultdict(dict)
        catalog: list[dict] = []
        total_tokens = 0

        for doc_number, document in enumerate(self._load_documents()):
            if limit is not None and doc_number >= limit:
                break

            tokens = tokenize(str(document.get("text") or ""))
            counts = Counter(tokens)
            total_tokens += len(tokens)

            catalog.append(self._catalog_record(document, doc_number, len(tokens)))
            for term, count in counts.items():
                postings[term][doc_number] = count

        document_count = len(catalog)
        if document_count == 0:
            raise ValueError("No documents available for indexing")

        # Pre-compute document vector norms for both required IDF methods.
        norm_squares = {
            method: [0.0] * document_count
            for method in SUPPORTED_IDF_METHODS
        }

        for term, term_postings in postings.items():
            df = len(term_postings)
            idf_values = {
                method: idf(method, document_count, df)
                for method in SUPPORTED_IDF_METHODS
            }
            for doc_number, raw_tf in term_postings.items():
                tf_weight = log_tf(raw_tf)
                for method, idf_value in idf_values.items():
                    weight = tf_weight * idf_value
                    norm_squares[method][doc_number] += weight * weight

        for doc_number, record in enumerate(catalog):
            record["vector_norms"] = {
                method: math.sqrt(norm_squares[method][doc_number])
                for method in SUPPORTED_IDF_METHODS
            }

        with self.paths.catalog_file.open("w", encoding="utf-8") as handle:
            for record in catalog:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        vocabulary = sorted(postings)
        with self.paths.vocabulary_file.open("w", encoding="utf-8") as handle:
            for term in vocabulary:
                handle.write(term + "\n")

        posting_count = 0
        with self.paths.index_file.open("w", encoding="utf-8") as handle:
            for term in vocabulary:
                term_postings = postings[term]
                posting_count += len(term_postings)
                record = {
                    "term": term,
                    "df": len(term_postings),
                    "postings": [
                        {"doc": doc_number, "tf": term_postings[doc_number]}
                        for doc_number in sorted(term_postings)
                    ],
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")

        stats = {
            "index_version": INDEX_VERSION,
            "document_count": document_count,
            "vocabulary_size": len(vocabulary),
            "posting_count": posting_count,
            "total_tokens": total_tokens,
            "average_document_tokens": round(total_tokens / document_count, 2),
            "idf_methods": list(SUPPORTED_IDF_METHODS),
            "tf_method": "1 + ln(tf)",
            "source_documents": str(
                self.paths.source_documents.relative_to(self.paths.project_root)
            ),
            "index_file": str(self.paths.index_file.relative_to(self.paths.project_root)),
            "catalog_file": str(self.paths.catalog_file.relative_to(self.paths.project_root)),
        }
        self.paths.stats_file.write_text(
            json.dumps(stats, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return stats
