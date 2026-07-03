import unittest

from langgraph.graph.state import CompiledStateGraph

from fin_rag.agent import FinRagAgent
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient


class LangGraphIntegrationTests(unittest.TestCase):
    def test_agent_uses_real_langgraph_when_installed(self):
        settings = Settings.from_env()
        client = GeminiClient(settings.api_key or "unused", settings.generation_model, settings.embedding_model)

        agent = FinRagAgent(client=client, retrieve=lambda _: [])

        self.assertIsInstance(agent.graph, CompiledStateGraph)


if __name__ == "__main__":
    unittest.main()
