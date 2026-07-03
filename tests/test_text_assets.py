from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TextAssetTests(unittest.TestCase):
    def test_key_text_assets_are_utf8_and_free_of_garbled_markers(self) -> None:
        asset_paths = [
            ROOT / "spec.md",
            ROOT / "corpus" / "README.md",
            ROOT / "eval" / "golden.yaml",
            ROOT / "src" / "fin_rag" / "prompts" / "system.md",
        ]

        for path in asset_paths:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("\ufffd", text, path.as_posix())
            self.assertNotIn("\u00b6", text, path.as_posix())


if __name__ == "__main__":
    unittest.main()
