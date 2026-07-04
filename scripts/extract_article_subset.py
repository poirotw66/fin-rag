from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.corpus import extract_articles


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract selected articles from a MOJ plain-text law file.")
    parser.add_argument("doc_id")
    parser.add_argument("articles", help="Comma-separated article headings, e.g. '第 2 條,第 5 條'")
    args = parser.parse_args()

    raw_dir = ROOT / "corpus" / "raw"
    source_path = raw_dir / f"{args.doc_id}.full.txt"
    if not source_path.exists():
        source_path = raw_dir / f"{args.doc_id}.txt"
    if not source_path.exists():
        print(f"missing source file for {args.doc_id}", file=sys.stderr)
        return 1

    wanted = [item.strip() for item in args.articles.split(",") if item.strip()]
    subset = extract_articles(source_path.read_text(encoding="utf-8"), wanted)
    if not subset.strip():
        print(f"no articles matched for {args.doc_id}", file=sys.stderr)
        return 1

    destination = raw_dir / f"{args.doc_id}.txt"
    destination.write_text(subset, encoding="utf-8")
    print(f"wrote {destination} ({len(wanted)} articles requested)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
