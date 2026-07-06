import os
import unittest

from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient


@unittest.skipUnless(os.environ.get("GEMINI_API_KEY"), "GEMINI_API_KEY not set")
class GeminiIntegrationTests(unittest.TestCase):
    def test_real_gemini_embedding_returns_vector(self):
        settings = Settings.from_env()
        self.assertTrue(settings.api_key, "GEMINI_API_KEY must be set in .env")
        client = GeminiClient(
            api_key=settings.api_key,
            generation_model=settings.generation_model,
            embedding_model=settings.embedding_model,
        )

        embedding = client.embed("金融機構防制洗錢辦法第 7 條")

        self.assertGreater(len(embedding), 10)
        self.assertIsInstance(embedding[0], float)

    def test_real_gemini_generation_returns_text(self):
        settings = Settings.from_env()
        self.assertTrue(settings.api_key, "GEMINI_API_KEY must be set in .env")
        client = GeminiClient(
            api_key=settings.api_key,
            generation_model=settings.generation_model,
            embedding_model=settings.embedding_model,
        )

        text = client.generate("請用繁體中文用一句話回答：CDD 是什麼？")

        self.assertGreater(len(text), 5)
