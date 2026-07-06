import unittest

from fin_rag.agent import FinRagAgent


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


if __name__ == "__main__":
    unittest.main()
