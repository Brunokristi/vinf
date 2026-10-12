from __future__ import annotations

import json
import heapq
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from indexer.idf import idf as calculate_idf, log_tf

from .query import ParsedQuery, parse_query
from .storage import RandomAccessJsonl, find_document_id


INDEX_DIR = Path("data/index")
INDEX_FILE = INDEX_DIR / "index.jsonl"
CATALOG_FILE = INDEX_DIR / "documents.jsonl"
SOURCE_FILE = Path("data/processed/documents.jsonl")

LEXICON_FILE = INDEX_DIR / "lexicon.json"
CATALOG_OFFSETS_FILE = INDEX_DIR / "catalog_offsets.json"
SOURCE_OFFSETS_FILE = INDEX_DIR / "source_offsets.json"
NORMS_FILE = INDEX_DIR / "document_norms.json"
ASSETS_FILE = INDEX_DIR / "search_assets.json"


@dataclass
class SearchResult:
    rank: int
    doc_key: str
    document_id: str | None
    score: float
    matched_terms: tuple[str, ...]
    catalog: dict[str, Any]
    source: dict[str, Any] | None = None


@dataclass
class SearchResponse:
    query: ParsedQuery
    idf_method: str
    elapsed_seconds: float
    total_hits: int
    results: list[SearchResult]


class SearchEngine:
    def __init__(self) -> None:
        self._assert_assets()

        self.lexicon = json.loads(LEXICON_FILE.read_text(encoding="utf-8"))

        catalog_assets = json.loads(
            CATALOG_OFFSETS_FILE.read_text(encoding="utf-8")
        )
        self.catalog_offsets = catalog_assets["offsets"]
        self.doc_to_document_id = catalog_assets.get(
            "doc_to_document_id",
            {},
        )

        self.source_offsets = json.loads(
            SOURCE_OFFSETS_FILE.read_text(encoding="utf-8")
        )
        self.norms = json.loads(
            NORMS_FILE.read_text(encoding="utf-8")
        )

        self.assets = json.loads(
            ASSETS_FILE.read_text(encoding="utf-8")
        )
        self.document_count = int(self.assets["document_count"])

        self.index_reader = RandomAccessJsonl(INDEX_FILE)
        self.catalog_reader = RandomAccessJsonl(CATALOG_FILE)
        self.source_reader = RandomAccessJsonl(SOURCE_FILE)

        self.postings_cache: dict[str, dict[str, int]] = {}

    def close(self) -> None:
        self.index_reader.close()
        self.catalog_reader.close()
        self.source_reader.close()

    def _assert_assets(self) -> None:
        required = (
            LEXICON_FILE,
            CATALOG_OFFSETS_FILE,
            SOURCE_OFFSETS_FILE,
            NORMS_FILE,
            ASSETS_FILE,
        )

        missing = [str(path) for path in required if not path.exists()]

        if missing:
            raise RuntimeError(
                "Search helper files do not exist yet.\n"
                "Run:\n\n"
                "    python -m searcher.prepare\n\n"
                f"Missing: {', '.join(missing)}"
            )

        assets = json.loads(ASSETS_FILE.read_text(encoding="utf-8"))

        for key, path in (
            ("index", INDEX_FILE),
            ("catalog", CATALOG_FILE),
            ("processed", SOURCE_FILE),
        ):
            expected = assets["sources"][key]
            stat = path.stat()

            if (
                stat.st_size != expected["size"]
                or stat.st_mtime_ns != expected["mtime_ns"]
            ):
                raise RuntimeError(
                    f"{path} changed after search assets were generated.\n"
                    "Run:\n\n"
                    "    python -m searcher.prepare"
                )

    def _idf(self, df: int, method: str) -> float:
        return calculate_idf(method, self.document_count, df)

    @staticmethod
    def _tf_weight(tf: int) -> float:
        return log_tf(tf)

    def _load_postings(self, term: str) -> dict[str, int]:
        if term in self.postings_cache:
            return self.postings_cache[term]

        entry = self.lexicon.get(term)

        if entry is None:
            self.postings_cache[term] = {}
            return {}

        record = self.index_reader.read(int(entry["offset"]))
        postings = record.get("postings", [])

        result = {
            str(posting["doc"]): int(posting["tf"])
            for posting in postings
        }

        # Small bounded cache. Query terms often repeat during demos.
        if len(self.postings_cache) >= 32:
            first_key = next(iter(self.postings_cache))
            self.postings_cache.pop(first_key, None)

        self.postings_cache[term] = result
        return result

    def _candidate_docs(
        self,
        query: ParsedQuery,
        term_postings: dict[str, dict[str, int]],
    ) -> set[str]:
        posting_sets = [
            set(term_postings[term])
            for term in query.terms
            if term_postings[term]
        ]

        if query.mode == "and":
            if len(posting_sets) != len(query.terms):
                return set()

            posting_sets.sort(key=len)

            candidates = posting_sets[0].copy()

            for docs in posting_sets[1:]:
                candidates.intersection_update(docs)

                if not candidates:
                    break

            return candidates

        candidates: set[str] = set()

        for docs in posting_sets:
            candidates.update(docs)

        return candidates

    def _query_weights(
        self,
        query: ParsedQuery,
        method: str,
    ) -> tuple[dict[str, float], float]:
        weights: dict[str, float] = {}

        for term in query.terms:
            entry = self.lexicon.get(term)

            if not entry:
                continue

            qtf = query.term_counts[term]
            qtf_weight = self._tf_weight(qtf)
            idf = self._idf(int(entry["df"]), method)
            weights[term] = qtf_weight * idf

        norm = math.sqrt(sum(weight * weight for weight in weights.values()))
        return weights, norm

    def _catalog(self, doc_key: str) -> dict[str, Any]:
        offset = self.catalog_offsets.get(doc_key)

        if offset is None:
            return {}

        return self.catalog_reader.read(int(offset))

    def _source(self, document_id: str | None) -> dict[str, Any] | None:
        if not document_id:
            return None

        offset = self.source_offsets.get(str(document_id))

        if offset is None:
            return None

        return self.source_reader.read(int(offset))

    def get_source_document(
        self,
        result: SearchResult,
    ) -> dict[str, Any] | None:
        if result.source is None:
            result.source = self._source(result.document_id)
        return result.source

    def search(
        self,
        query_text: str,
        *,
        idf_method: str = "classic",
        mode: str | None = None,
        limit: int = 10,
        load_sources: bool = True,
    ) -> SearchResponse:
        started = time.perf_counter()

        query = parse_query(query_text, forced_mode=mode)

        term_postings = {
            term: self._load_postings(term)
            for term in query.terms
        }

        candidates = self._candidate_docs(query, term_postings)

        query_weights, query_norm = self._query_weights(
            query,
            idf_method,
        )

        scored: list[tuple[float, str, tuple[str, ...]]] = []

        if query_norm > 0:
            for doc_key in candidates:
                norm_record = self.norms.get(doc_key)

                if not norm_record:
                    continue

                document_norm = float(norm_record[idf_method])

                if document_norm <= 0:
                    continue

                dot = 0.0
                matched = []

                for term in query.terms:
                    tf = term_postings[term].get(doc_key, 0)

                    if tf <= 0:
                        continue

                    matched.append(term)

                    entry = self.lexicon[term]
                    idf = self._idf(int(entry["df"]), idf_method)
                    document_weight = self._tf_weight(tf) * idf
                    dot += query_weights.get(term, 0.0) * document_weight

                score = dot / (query_norm * document_norm)

                if score > 0:
                    scored.append(
                        (
                            score,
                            doc_key,
                            tuple(matched),
                        )
                    )

        top_scored = heapq.nsmallest(
            limit,
            scored,
            key=lambda item: (-item[0], item[1]),
        )

        results: list[SearchResult] = []

        for rank, (score, doc_key, matched) in enumerate(
            top_scored,
            start=1,
        ):
            catalog = self._catalog(doc_key)
            document_id = (
                self.doc_to_document_id.get(doc_key)
                or find_document_id(catalog)
            )

            result = SearchResult(
                rank=rank,
                doc_key=doc_key,
                document_id=document_id,
                score=score,
                matched_terms=matched,
                catalog=catalog,
            )

            if load_sources:
                result.source = self._source(document_id)

            results.append(result)

        elapsed = time.perf_counter() - started

        return SearchResponse(
            query=query,
            idf_method=idf_method,
            elapsed_seconds=elapsed,
            total_hits=len(scored),
            results=results,
        )

    def explain(
        self,
        response: SearchResponse,
        result: SearchResult,
    ) -> dict[str, Any]:
        query = response.query

        term_postings = {
            term: self._load_postings(term)
            for term in query.terms
        }

        methods = {}

        for method in ("classic", "smooth"):
            query_weights, query_norm = self._query_weights(
                query,
                method,
            )

            document_norm = float(
                self.norms[result.doc_key][method]
            )

            rows = []
            dot = 0.0

            for term in query.terms:
                entry = self.lexicon.get(term)

                if not entry:
                    continue

                df = int(entry["df"])
                qtf = int(query.term_counts[term])
                dtf = int(
                    term_postings[term].get(
                        result.doc_key,
                        0,
                    )
                )

                qtf_weight = self._tf_weight(qtf)
                dtf_weight = self._tf_weight(dtf)
                idf = self._idf(df, method)
                query_weight = qtf_weight * idf
                document_weight = dtf_weight * idf
                contribution = query_weight * document_weight

                dot += contribution

                rows.append(
                    {
                        "term": term,
                        "qtf": qtf,
                        "dtf": dtf,
                        "df": df,
                        "qtf_weight": qtf_weight,
                        "dtf_weight": dtf_weight,
                        "idf": idf,
                        "query_weight": query_weight,
                        "document_weight": document_weight,
                        "contribution": contribution,
                    }
                )

            denominator = query_norm * document_norm
            score = dot / denominator if denominator else 0.0

            methods[method] = {
                "rows": rows,
                "query_norm": query_norm,
                "document_norm": document_norm,
                "dot_product": dot,
                "denominator": denominator,
                "score": score,
            }

        return {
            "document_count": self.document_count,
            "query": query.display,
            "mode": query.mode,
            "rank": result.rank,
            "selected_idf": response.idf_method,
            "selected_score": result.score,
            "matched_terms": result.matched_terms,
            "methods": methods,
        }
