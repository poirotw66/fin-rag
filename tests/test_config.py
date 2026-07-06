import unittest

from fin_rag.config import Settings


class SettingsTests(unittest.TestCase):
    def test_settings_default_to_gemini_models(self):
        settings = Settings.from_env({})

        self.assertEqual(settings.generation_model, "gemini-2.5-flash")
        self.assertEqual(settings.embedding_model, "gemini-embedding-2")
        self.assertEqual(settings.retrieval_mode, "hybrid")
        self.assertEqual(settings.vector_backend, "auto")
        self.assertEqual(settings.min_retrieval_score, 0.028)
        self.assertEqual(settings.max_retrieval_rounds, 1)

    def test_settings_reads_api_key_and_model_overrides(self):
        settings = Settings.from_env(
            {
                "GEMINI_API_KEY": "secret",
                "FIN_RAG_GENERATION_MODEL": "custom-generation",
                "FIN_RAG_EMBEDDING_MODEL": "custom-embedding",
                "FIN_RAG_RETRIEVAL_MODE": "embedding",
            }
        )

        self.assertEqual(settings.api_key, "secret")
        self.assertEqual(settings.generation_model, "custom-generation")
        self.assertEqual(settings.embedding_model, "custom-embedding")
        self.assertEqual(settings.retrieval_mode, "embedding")

    def test_settings_rejects_unknown_retrieval_mode(self) -> None:
        with self.assertRaises(ValueError):
            Settings.from_env({"FIN_RAG_RETRIEVAL_MODE": "bm25-only"})

    def test_settings_rejects_unknown_vector_backend(self) -> None:
        with self.assertRaises(ValueError):
            Settings.from_env({"FIN_RAG_VECTOR_BACKEND": "pinecone"})


    def test_settings_rejects_negative_retrieval_rounds(self) -> None:
        with self.assertRaises(ValueError):
            Settings.from_env({"FIN_RAG_MAX_RETRIEVAL_ROUNDS": "-1"})


if __name__ == "__main__":
    unittest.main()
