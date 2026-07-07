import unittest

from fin_rag.agent import FinRagAgent, REFUSAL_LOW_RETRIEVAL
from fin_rag.types import Chunk, RetrievedChunk


class QueryRewriteTests(unittest.TestCase):
    def test_rewrite_query_node_passes_model_output_to_retriever(self) -> None:
        captured: dict[str, list[str]] = {}

        class FakeClient:
            def generate(self, prompt: str) -> str:
                return "證券投資信託基金管理辦法 利害關係人 基金 證券"

            def embed(self, text: str) -> list[float]:
                return [1.0]

        def retrieve_queries(queries: list[str]) -> list:
            captured["queries"] = queries
            return []

        agent = FinRagAgent(
            client=FakeClient(),
            retrieve=lambda _: [],
            retrieve_queries=retrieve_queries,
        )
        state = agent._classify_node({"question": "基金能否買賣利害關係公司發行之證券？"})
        state = agent._rewrite_query_node(state)
        agent._retrieve_node(state)

        self.assertIn("證券投資信託基金管理辦法", captured["queries"][1])

    def test_rewrite_falls_back_to_original_question_when_model_returns_empty(self) -> None:
        class FakeClient:
            def generate(self, prompt: str) -> str:
                return "   "

            def embed(self, text: str) -> list[float]:
                return [1.0]

        agent = FinRagAgent(client=FakeClient(), retrieve=lambda _: [])
        question = "什麼是風險基礎方法？"
        self.assertEqual(agent._rewrite_for_retrieval(question), [question])

    def test_assess_retrieval_refuses_when_score_below_threshold_and_no_retries_left(self) -> None:
        chunk = Chunk(
            doc_id="aml-finst",
            title="aml-finst",
            article="第 2 條",
            text="text",
            track="test",
            source_url="https://example.test",
            revision_date="113-01-01",
        )

        class FakeClient:
            def generate(self, prompt: str) -> str:
                return "洗錢防制"

            def embed(self, text: str) -> list[float]:
                return [1.0]

        agent = FinRagAgent(
            client=FakeClient(),
            retrieve=lambda _: [],
            retrieve_queries=lambda _: [RetrievedChunk(chunk, 0.01)],
            min_retrieval_score=0.028,
            max_retrieval_rounds=0,
        )
        state = {
            "question": "什麼是風險基礎方法？",
            "retrieval_round": 0,
            "retrieved": [RetrievedChunk(chunk, 0.01)],
        }
        state = agent._assess_retrieval_node(state)

        self.assertFalse(state["retrieval_sufficient"])
        self.assertEqual(state["refusal_reason"], "low_retrieval")
        self.assertEqual(agent._route_after_assess(state), "refuse")

    def test_refuse_node_uses_low_retrieval_message(self) -> None:
        agent = FinRagAgent(client=type("C", (), {"generate": lambda *_: ""})(), retrieve=lambda _: [])
        state = agent._refuse_node({"refusal_reason": "low_retrieval"})

        self.assertEqual(state["answer"], REFUSAL_LOW_RETRIEVAL)
        self.assertTrue(state["refused"])

    def test_route_after_citation_retries_generation_before_refusal(self) -> None:
        agent = FinRagAgent(client=type("C", (), {"generate": lambda *_: ""})(), retrieve=lambda _: [])
        state = {
            "citation_hit": False,
            "citation_retry_count": 0,
            "answer": "missing citation",
        }

        self.assertEqual(agent._route_after_citation(state), "generate")
        self.assertEqual(state["citation_retry_count"], 1)
        self.assertIn("上一輪回答未通過引用檢查", state["generation_retry_note"])

    def test_route_after_citation_refuses_after_max_attempts(self) -> None:
        agent = FinRagAgent(client=type("C", (), {"generate": lambda *_: ""})(), retrieve=lambda _: [])
        state = {
            "citation_hit": False,
            "citation_retry_count": 2,
            "answer": "still missing citation",
        }

        self.assertEqual(agent._route_after_citation(state), "refuse")
        self.assertEqual(state["refusal_reason"], "citation")

    def test_route_after_citation_retries_policy_misrefusal_without_citation_budget(self) -> None:
        agent = FinRagAgent(client=type("C", (), {"generate": lambda *_: ""})(), retrieve=lambda _: [])
        policy_answer = (
            "我不能判斷特定個案的裁罰金額、賠償責任或刑事責任。"
            "以下回答僅能依公開法規提供一般程序與條文方向，且不構成法律意見。"
        )
        state = {
            "question": "全委帳戶與基金對利害關係人交易限制有何不同？",
            "citation_hit": False,
            "citation_retry_count": 2,
            "policy_misrefusal_count": 0,
            "answer": policy_answer,
        }

        self.assertEqual(agent._route_after_citation(state), "generate")
        self.assertEqual(state["policy_misrefusal_count"], 1)
        self.assertIn("不可拒答", state["generation_retry_note"])


if __name__ == "__main__":
    unittest.main()
