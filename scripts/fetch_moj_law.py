from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pcode")
    parser.add_argument("doc_id")
    args = parser.parse_args()
    url = f"https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={args.pcode}"
    destination = ROOT / "corpus" / "raw" / f"{args.doc_id}.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as response:
        destination.write_bytes(response.read())
    print(f"wrote {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

