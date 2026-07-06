from __future__ import annotations

from .types import RetrievedChunk


def retrieval_confidence(retrieved: list[RetrievedChunk]) -> float:
    if not retrieved:
        return 0.0
    return max(item.score for item in retrieved)


def is_retrieval_sufficient(confidence: float, *, min_score: float) -> bool:
    return confidence >= min_score


def merge_retrieved_chunks(
    existing: list[RetrievedChunk],
    new_items: list[RetrievedChunk],
) -> list[RetrievedChunk]:
    merged: dict[tuple[str, str], RetrievedChunk] = {}
    for item in [*existing, *new_items]:
        key = (item.chunk.doc_id, item.chunk.article)
        current = merged.get(key)
        if current is None or item.score > current.score:
            merged[key] = item
    return sorted(merged.values(), key=lambda chunk: chunk.score, reverse=True)
