from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .bm25 import BM25Index, read_bm25_index, write_bm25_index
from .faiss_store import FaissChunkIndex, faiss_paths_for, read_faiss_index, write_faiss_index
from .types import Chunk, RetrievedChunk


@dataclass(frozen=True)
class VectorRecord:
    chunk: Chunk
    embedding: list[float]


@dataclass(frozen=True)
class LoadedIndex:
    chunks: list[Chunk]
    records: list[VectorRecord] | None
    faiss_index: FaissChunkIndex | None


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


def load_index_bundle(index_jsonl_path: str | Path, *, backend: str = "auto") -> LoadedIndex:
    jsonl_path = Path(index_jsonl_path)
    faiss_path, meta_path = faiss_paths_for(jsonl_path)
    use_faiss = backend == "faiss" or (backend == "auto" and faiss_path.exists() and meta_path.exists())
    if use_faiss:
        if not faiss_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"FAISS index requires {faiss_path} and {meta_path}")
        faiss_index = read_faiss_index(faiss_path, meta_path)
        return LoadedIndex(chunks=faiss_index.chunks, records=None, faiss_index=faiss_index)
    records = read_index(jsonl_path)
    return LoadedIndex(
        chunks=[record.chunk for record in records],
        records=records,
        faiss_index=None,
    )


def write_faiss_bundle(records: list[VectorRecord], index_jsonl_path: str | Path) -> None:
    faiss_path, meta_path = faiss_paths_for(index_jsonl_path)
    write_faiss_index(
        [record.chunk for record in records],
        [record.embedding for record in records],
        faiss_path,
        meta_path,
    )


def bm25_path_for(index_jsonl_path: str | Path) -> Path:
    return Path(index_jsonl_path).parent / "index_bm25.json"


def chunk_search_text(chunk: Chunk) -> str:
    return f"{chunk.title} {chunk.article} {chunk.text}"


def write_bm25_bundle(records: list[VectorRecord], index_jsonl_path: str | Path) -> None:
    index = BM25Index.build([chunk_search_text(record.chunk) for record in records])
    write_bm25_index(index, bm25_path_for(index_jsonl_path))


def search(records: list[VectorRecord], query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
    ranked = rank_by_embedding(records, query_embedding)
    return ranked[:top_k]


def search_loaded_index(
    bundle: LoadedIndex,
    query_embedding: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    if bundle.faiss_index is not None:
        return bundle.faiss_index.search(query_embedding, top_k)
    if bundle.records is None:
        return []
    return search(bundle.records, query_embedding, top_k)


def hybrid_search_loaded_index(
    bundle: LoadedIndex,
    query_embedding: list[float],
    query_text: str,
    top_k: int,
    *,
    bm25_index: BM25Index,
    rrf_k: int = 60,
) -> list[RetrievedChunk]:
    if not bundle.chunks:
        return []
    if len(bundle.chunks) != len(bm25_index.corpus):
        raise ValueError("BM25 index size must match chunk count")
    if bundle.faiss_index is not None:
        embedding_order = [index for index, _ in bundle.faiss_index.rank_all(query_embedding)]
    elif bundle.records is not None:
        embedding_order = [
            index
            for index, _ in sorted(
                enumerate(bundle.records),
                key=lambda item: cosine_similarity(query_embedding, item[1].embedding),
                reverse=True,
            )
        ]
    else:
        return []
    return _hybrid_fuse(bundle.chunks, embedding_order, query_text, top_k, bm25_index, rrf_k)


def rank_by_embedding(records: list[VectorRecord], query_embedding: list[float]) -> list[RetrievedChunk]:
    ranked = [
        RetrievedChunk(chunk=record.chunk, score=cosine_similarity(query_embedding, record.embedding))
        for record in records
    ]
    ranked.sort(key=lambda item: item.score, reverse=True)
    return ranked


def rank_loaded_index(bundle: LoadedIndex, query_embedding: list[float]) -> list[RetrievedChunk]:
    if bundle.faiss_index is not None:
        return [
            RetrievedChunk(chunk=bundle.chunks[index], score=score)
            for index, score in bundle.faiss_index.rank_all(query_embedding)
        ]
    if bundle.records is None:
        return []
    return rank_by_embedding(bundle.records, query_embedding)


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
    embedding_order = [
        index
        for index, _ in sorted(
            enumerate(records),
            key=lambda item: cosine_similarity(query_embedding, item[1].embedding),
            reverse=True,
        )
    ]
    chunks = [record.chunk for record in records]
    return _hybrid_fuse(chunks, embedding_order, query_text, top_k, bm25_index, rrf_k)


def _hybrid_fuse(
    chunks: list[Chunk],
    embedding_order: list[int],
    query_text: str,
    top_k: int,
    bm25_index: BM25Index,
    rrf_k: int,
) -> list[RetrievedChunk]:
    bm25_scores = bm25_index.score(query_text)
    bm25_order = sorted(range(len(chunks)), key=lambda index: bm25_scores[index], reverse=True)
    fused_scores = [0.0] * len(chunks)
    for rank, index in enumerate(embedding_order):
        fused_scores[index] += 1.0 / (rrf_k + rank + 1)
    for rank, index in enumerate(bm25_order):
        fused_scores[index] += 1.0 / (rrf_k + rank + 1)
    selected = sorted(range(len(chunks)), key=lambda index: fused_scores[index], reverse=True)[:top_k]
    return [RetrievedChunk(chunk=chunks[index], score=fused_scores[index]) for index in selected]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)

