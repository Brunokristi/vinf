from __future__ import annotations

import math


SUPPORTED_IDF_METHODS = ("classic", "smooth")


def classic_idf(document_count: int, document_frequency: int) -> float:
    """Classic non-probabilistic IDF: ln(N / df)."""
    if document_count <= 0:
        raise ValueError("document_count must be greater than zero")
    if document_frequency <= 0 or document_frequency > document_count:
        raise ValueError("document_frequency must be in the range 1..N")
    return math.log(document_count / document_frequency)


def smooth_idf(document_count: int, document_frequency: int) -> float:
    """Smoothed non-probabilistic IDF: ln((N + 1) / (df + 1)) + 1."""
    if document_count <= 0:
        raise ValueError("document_count must be greater than zero")
    if document_frequency <= 0 or document_frequency > document_count:
        raise ValueError("document_frequency must be in the range 1..N")
    return math.log((document_count + 1) / (document_frequency + 1)) + 1.0


def idf(method: str, document_count: int, document_frequency: int) -> float:
    if method == "classic":
        return classic_idf(document_count, document_frequency)
    if method == "smooth":
        return smooth_idf(document_count, document_frequency)
    raise ValueError(
        f"Unknown IDF method {method!r}. Supported: {', '.join(SUPPORTED_IDF_METHODS)}"
    )


def log_tf(term_frequency: int) -> float:
    """Sublinear TF used for vector weights: 1 + ln(tf), or 0 when absent."""
    if term_frequency < 0:
        raise ValueError("term_frequency cannot be negative")
    if term_frequency == 0:
        return 0.0
    return 1.0 + math.log(term_frequency)
