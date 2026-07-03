from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.corpus import chunk_text_by_article, load_manifest, write_chunks_jsonl
from fin_rag.cli import configure_utf8_stdio


def main() -> int:
    configure_utf8_stdio()
    manifest = load_manifest(ROOT / "corpus" / "manifest.json")
    chunks = []
    for entry in manifest.values():
        raw_path = ROOT / "corpus" / "raw" / f"{entry.doc_id}.{entry.format}"
        if not raw_path.exists():
            print(f"missing raw file: {raw_path}", file=sys.stderr)
            return 1
        chunks.extend(
            chunk_text_by_article(
                doc_id=entry.doc_id,
                title=entry.title,
                track=entry.track,
                source_url=entry.source_url,
                revision_date=entry.revision_date,
                text=raw_path.read_text(encoding="utf-8"),
            )
        )
    write_chunks_jsonl(chunks, ROOT / "corpus" / "chunks.jsonl")
    print(f"wrote {len(chunks)} chunks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
