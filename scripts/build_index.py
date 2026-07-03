from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.config import Settings
from fin_rag.corpus import read_chunks_jsonl
from fin_rag.cli import configure_utf8_stdio
from fin_rag.gemini import GeminiClient
from fin_rag.vector_store import VectorRecord, write_index


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
    chunks = read_chunks_jsonl(ROOT / "corpus" / "chunks.jsonl")
    records = []
    for index, chunk in enumerate(chunks, start=1):
        print(f"embedding {index}/{len(chunks)} {chunk.doc_id} {chunk.article}")
        records.append(VectorRecord(chunk=chunk, embedding=client.embed(f"{chunk.title} {chunk.article} {chunk.text}")))
    write_index(records, ROOT / "corpus" / "index.jsonl")
    print(f"wrote {len(records)} vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
