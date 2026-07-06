import unittest

try:
    from langgraph.graph.state import CompiledStateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

from fin_rag.agent import FinRagAgent
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient


@unittest.skipUnless(LANGGRAPH_AVAILABLE, "langgraph not installed")
class LangGraphIntegrationTests(unittest.TestCase):
    def test_agent_uses_real_langgraph_when_installed(self) -> None:
        settings = Settings.from_env()
        client = GeminiClient(
            settings.api_key or "unused",
            settings.generation_model,
            settings.embedding_model,
        )

        agent = FinRagAgent(client=client, retrieve=lambda _: [])

        self.assertIsInstance(agent.graph, CompiledStateGraph)


if __name__ == "__main__":
    unittest.main()
