import json
import tempfile
import unittest
from pathlib import Path

from fin_rag.corpus import chunk_text_by_article, load_manifest


class CorpusTests(unittest.TestCase):
    def test_load_manifest_returns_entries_by_doc_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "doc_id": "sit-fund-mgmt",
                            "title": "證券投資信託基金管理辦法",
                            "source_url": "https://example.test/law",
                            "issuer": "金融監督管理委員會",
                            "revision_date": "113-01-01",
                            "fetched_at": "2026-06-25",
                            "format": "txt",
                            "chunk_strategy": "by_article",
                            "track": "sit-related-party",
                        }
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            manifest = load_manifest(path)

        self.assertEqual(manifest["sit-fund-mgmt"].track, "sit-related-party")
        self.assertEqual(manifest["sit-fund-mgmt"].title, "證券投資信託基金管理辦法")

    def test_chunk_text_by_article_keeps_article_metadata(self):
        text = "第 10 條\n基金不得投資於利害關係公司發行之證券。\n第 11 條\n本辦法所稱利害關係公司如下。"

        chunks = chunk_text_by_article(
            doc_id="sit-fund-mgmt",
            title="證券投資信託基金管理辦法",
            track="sit-related-party",
            source_url="https://example.test/law",
            revision_date="113-01-01",
            text=text,
        )

        self.assertEqual([chunk.article for chunk in chunks], ["第 10 條", "第 11 條"])
        self.assertIn("不得投資", chunks[0].text)
        self.assertEqual(chunks[0].doc_id, "sit-fund-mgmt")


if __name__ == "__main__":
    unittest.main()
