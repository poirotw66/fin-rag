import unittest

from fin_rag.citations import citation_hit, looks_like_policy_refusal, should_refuse_question
from fin_rag.types import Chunk, RetrievedChunk


class CitationTests(unittest.TestCase):
    def test_citation_hit_requires_retrieved_doc_and_article(self):
        retrieved = [
            RetrievedChunk(
                chunk=Chunk(
                    doc_id="sit-fund-mgmt",
                    title="證券投資信託基金管理辦法",
                    article="第 10 條",
                    text="基金不得投資利害關係公司證券。",
                    track="sit-related-party",
                    source_url="https://example.test",
                    revision_date="113-01-01",
                ),
                score=0.9,
            )
        ]
        securities_retrieved = [
            RetrievedChunk(
                chunk=Chunk(
                    doc_id="sit-securities-act",
                    title="證券交易法（關係人／董事義務節錄）",
                    article="第 14-2 條",
                    text="獨立董事應保持獨立性。",
                    track="sit-related-party",
                    source_url="https://example.test",
                    revision_date="113-01-01",
                ),
                score=0.8,
            )
        ]

        self.assertTrue(citation_hit("不得投資（sit-fund-mgmt 第 10 條）。", retrieved))
        self.assertTrue(citation_hit("不得投資（證券投資信託基金管理辦法第10條）。", retrieved))
        self.assertTrue(citation_hit("不得投資 sit-fund-mgmt 第 10 條。", retrieved))
        self.assertTrue(citation_hit("限制（sit-securities-act 第 14-2 條）。", securities_retrieved))
        self.assertFalse(citation_hit("不得投資（sit-fund-mgmt 第 11 條）。", retrieved))

    def test_should_refuse_case_specific_penalty_questions(self):
        self.assertTrue(should_refuse_question("國泰投信會被罰多少？"))
        self.assertTrue(should_refuse_question("全委帳戶 4.54 億損失由誰賠？"))
        self.assertFalse(should_refuse_question("CDD 要做哪些事？"))

    def test_looks_like_policy_refusal_detects_standard_disclaimer(self) -> None:
        self.assertTrue(
            looks_like_policy_refusal(
                "我不能判斷特定個案的裁罰金額、賠償責任或刑事責任。"
            )
        )
        self.assertFalse(looks_like_policy_refusal("依 sit-fund-mgmt 第 10 條，基金不得投資利害關係公司證券。"))


if __name__ == "__main__":
    unittest.main()
