from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from .bm25 import BM25Index
from .types import Chunk, RetrievedChunk


@dataclass(frozen=True)
class VectorRecord:
    chunk: Chunk
    embedding: list[float]


def write_index(records: list[VectorRecord], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(
                json.dumps(
                    {"chunk": record.chunk.to_json(), "embedding": record.embedding},
                    ensure_ascii=False,
                )
                + "\n"
            )


def read_index(path: str | Path) -> list[VectorRecord]:
    source = Path(path)
    if not source.exists():
        return []
    records = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if line.strip():
            data = json.loads(line)
            records.append(VectorRecord(chunk=Chunk.from_json(data["chunk"]), embedding=[float(x) for x in data["embedding"]]))
    return records


def search(records: list[VectorRecord], query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    ranked = [
        RetrievedChunk(chunk=record.chunk, score=cosine_similarity(query_embedding, record.embedding))
        for record in records
    ]
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked[:top_k]


def hybrid_search(
    records: list[VectorRecord],
    query_embedding: list[float],
    query_text: str,
    top_k: int,
    *,
    bm25_index: BM25Index,
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    if not records:
        return []
    if len(records) != len(bm25_index.corpus):
        raise ValueError("BM25 index size must match vector records")

    embedding_order = sorted(
        range(len(records)),
        key=lambda index: cosine_similarity(query_embedding, records[index].embedding),
        reverse=True,
    )
    bm25_scores = bm25_index.score(query_text)
    bm25_order = sorted(range(len(records)), key=lambda index: bm25_scores[index], reverse=True)

    fused_scores = [0.0] * len(records)
    for rank, index in enumerate(embedding_order):
        fused_scores[index] += 1.0 / (rrf_k + rank + 1)
    for rank, index in enumerate(bm25_order):
        fused_scores[index] += 1.0 / (rrf_k + rank + 1)

    selected = sorted(range(len(records)), key=lambda index: fused_scores[index], reverse=True)[:top_k]
    return [RetrievedChunk(chunk=records[index].chunk, score=fused_scores[index]) for index in selected]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)

