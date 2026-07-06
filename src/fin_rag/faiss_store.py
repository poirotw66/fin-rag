from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from .types import Chunk, RetrievedChunk


@dataclass(frozen=True)
class FaissChunkIndex:
    chunks: list[Chunk]
    index: Any

    def search(self, query_embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        if not self.chunks:
            return []
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, min(top_k, self.index.ntotal))
        results: list[RetrievedChunk] = []
        for index, score in zip(indices[0], scores[0]):
            if index < 0:
                continue
            results.append(
                RetrievedChunk(chunk=self.chunks[int(index)], score=float(score))
            )
        return results

    def rank_all(self, query_embedding: list[float]) -> list[tuple[int, float]]:
        if not self.chunks:
            return []
        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, self.index.ntotal)
        ranked = [
            (int(index), float(score))
            for index, score in zip(indices[0], scores[0])
            if index >= 0
        ]
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked


def write_faiss_index(
    chunks: list[Chunk],
    embeddings: list[list[float]],
    faiss_path: str | Path,
    meta_path: str | Path,
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("chunk and embedding counts must match")
    destination = Path(faiss_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    meta_destination = Path(meta_path)
    if not chunks:
        if destination.exists():
            destination.unlink()
        meta_destination.write_text("", encoding="utf-8")
        return
    vectors = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    faiss.write_index(index, str(destination))
    with meta_destination.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps({"chunk": chunk.to_json()}, ensure_ascii=False) + "\n")


def read_faiss_index(faiss_path: str | Path, meta_path: str | Path) -> FaissChunkIndex:
    index = faiss.read_index(str(faiss_path))
    chunks: list[Chunk] = []
    for line in Path(meta_path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            chunks.append(Chunk.from_json(json.loads(line)["chunk"]))
    if index.ntotal != len(chunks):
        raise ValueError("faiss index row count does not match metadata")
    return FaissChunkIndex(chunks=chunks, index=index)


def faiss_paths_for(index_jsonl_path: str | Path) -> tuple[Path, Path]:
    corpus_dir = Path(index_jsonl_path).parent
    return corpus_dir / "index.faiss", corpus_dir / "index_meta.jsonl"
