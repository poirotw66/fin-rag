from __future__ import annotations

import json
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class CorpusCoverageTests(unittest.TestCase):
    def test_every_manifest_entry_has_raw_file(self) -> None:
        manifest = json.loads((ROOT / "corpus" / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest:
            raw_path = ROOT / "corpus" / "raw" / f"{entry['doc_id']}.{entry['format']}"
            self.assertTrue(raw_path.exists(), f"missing raw file: {raw_path}")

    def test_spot_check_articles_exist_in_chunks(self) -> None:
        spot_check = yaml.safe_load((ROOT / "corpus" / "spot_check.yaml").read_text(encoding="utf-8"))
        articles_by_doc: dict[str, set[str]] = {}
        for line in (ROOT / "corpus" / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            articles_by_doc.setdefault(row["doc_id"], set()).add(row["article"])
        for doc_id, required in spot_check.items():
            found = articles_by_doc.get(doc_id, set())
            for article in required:
                self.assertIn(article, found, f"{doc_id} missing {article}")


if __name__ == "__main__":
    unittest.main()
