from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    spot_check = yaml.safe_load((ROOT / "corpus" / "spot_check.yaml").read_text(encoding="utf-8"))
    articles_by_doc: dict[str, set[str]] = {}
    chunks_path = ROOT / "corpus" / "chunks.jsonl"
    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        articles_by_doc.setdefault(row["doc_id"], set()).add(row["article"])
    missing = []
    for doc_id, required in spot_check.items():
        found = articles_by_doc.get(doc_id, set())
        for article in required:
            if article not in found:
                missing.append(f"{doc_id} {article}")
    if missing:
        print("MISSING:", *missing, sep="\n  ")
        return 1
    print(f"OK: {sum(len(v) for v in articles_by_doc.values())} chunks, spot-check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
