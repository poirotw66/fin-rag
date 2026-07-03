from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from fin_rag.agent import AgentResult
from fin_rag.types import Chunk, RetrievedChunk
from scripts.ask import format_result


def _chunk(*, doc_id: str, article: str, title: str, text: str, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            doc_id=doc_id,
            title=title,
            article=article,
            text=text,
            track="A",
            source_url="https://example.com",
            revision_date="2026-01-01",
        ),
        score=score,
    )


class AskScriptTests(unittest.TestCase):
    def test_format_result_includes_answer_refusal_citations_and_chunk_summaries(self) -> None:
        result = AgentResult(
            answer="客戶身分確認應辨識實質受益人。（aml-finst 第 7 條）",
            refused=False,
            citation_hit=True,
            retrieved=[
                _chunk(
                    doc_id="aml-finst",
                    article="第 7 條",
                    title="金融機構防制洗錢辦法",
                    text="金融機構應進行客戶身分確認，包含確認客戶身分、辨識實質受益人，並瞭解業務關係目的與性質。",
                ),
                _chunk(
                    doc_id="aml-finst",
                    article="第 12 條",
                    title="金融機構防制洗錢辦法",
                    text="金融機構對交易紀錄及憑證應依規定保存。",
                    score=0.7,
                ),
            ],
        )

        rendered = format_result(result)

        self.assertIn("Answer", rendered)
        self.assertIn("Refused: no", rendered)
        self.assertIn("Citations", rendered)
        self.assertIn("- aml-finst / 第 7 條 / 金融機構防制洗錢辦法", rendered)
        self.assertIn("Retrieved Chunks", rendered)
        self.assertIn("[1] aml-finst / 第 7 條", rendered)
        self.assertIn("score=0.90", rendered)
        self.assertIn("金融機構應進行客戶身分確認", rendered)

    def test_format_result_marks_refusal_yes(self) -> None:
        result = AgentResult(
            answer="我不能判斷特定個案的裁罰金額。",
            refused=True,
            citation_hit=False,
            retrieved=[],
        )

        rendered = format_result(result)

        self.assertIn("Refused: yes", rendered)
        self.assertIn("Citations", rendered)
        self.assertIn("- none", rendered)
        self.assertIn("Retrieved Chunks", rendered)


if __name__ == "__main__":
    unittest.main()
