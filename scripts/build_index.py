from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.config import Settings
from fin_rag.corpus import read_chunks_jsonl
from fin_rag.cli import configure_utf8_stdio
from fin_rag.gemini import GeminiClient
from fin_rag.vector_store import VectorRecord, read_index, write_bm25_bundle, write_faiss_bundle, write_index


def main() -> int:
    configure_utf8_stdio()
    settings = Settings.from_env()
    if not settings.api_key:
        print("GEMINI_API_KEY is required in .env", file=sys.stderr)
        return 1
    client = GeminiClient(
        api_key=settings.api_key,
        generation_model=settings.generation_model,
        embedding_model=settings.embedding_model,
    )
    index_path = ROOT / "corpus" / "index.jsonl"
    existing = {
        _record_key(record): record
        for record in read_index(index_path)
    }
    chunks = read_chunks_jsonl(ROOT / "corpus" / "chunks.jsonl")
    records: list[VectorRecord] = []
    reused = 0
    for index, chunk in enumerate(chunks, start=1):
        key = _chunk_key(chunk)
        cached = existing.get(key)
        if cached is not None and cached.chunk.text == chunk.text:
            records.append(cached)
            reused += 1
            print(f"reuse {index}/{len(chunks)} {chunk.doc_id} {chunk.article}")
            continue
        print(f"embedding {index}/{len(chunks)} {chunk.doc_id} {chunk.article}")
        records.append(
            VectorRecord(
                chunk=chunk,
                embedding=client.embed(f"{chunk.title} {chunk.article} {chunk.text}"),
            )
        )
    write_index(records, index_path)
    write_faiss_bundle(records, index_path)
    write_bm25_bundle(records, index_path)
    print(f"wrote {len(records)} vectors ({reused} reused)")
    print(f"wrote FAISS index at {index_path.parent / 'index.faiss'}")
    print(f"wrote BM25 index at {index_path.parent / 'index_bm25.json'}")
    return 0


def _chunk_key(chunk) -> tuple[str, str]:
    return chunk.doc_id, chunk.article


def _record_key(record: VectorRecord) -> tuple[str, str]:
    return record.chunk.doc_id, record.chunk.article


if __name__ == "__main__":
    raise SystemExit(main())
