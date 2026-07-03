from __future__ import annotations

# pylint: disable=import-error

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.cli import configure_utf8_stdio
from fin_rag.moj import parse_moj_law_html


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("doc_id")
    args = parser.parse_args()

    configure_utf8_stdio()
    raw_dir = ROOT / "corpus" / "raw"
    html_path = raw_dir / f"{args.doc_id}.html"
    txt_path = raw_dir / f"{args.doc_id}.txt"

    document = parse_moj_law_html(html_path.read_text(encoding="utf-8"))
    txt_path.write_text(f"{document.text}\n", encoding="utf-8")
    print(f"wrote {txt_path}")
    print(f"title: {document.title}")
    print(f"revision_date: {document.revision_date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
