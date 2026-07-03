import unittest

from fin_rag.config import Settings


class SettingsTests(unittest.TestCase):
    def test_settings_default_to_gemini_models(self):
        settings = Settings.from_env({})

        self.assertEqual(settings.generation_model, "gemini-2.5-flash")
        self.assertEqual(settings.embedding_model, "gemini-embedding-2")

    def test_settings_reads_api_key_and_model_overrides(self):
        settings = Settings.from_env(
            {
                "GEMINI_API_KEY": "secret",
                "FIN_RAG_GENERATION_MODEL": "custom-generation",
                "FIN_RAG_EMBEDDING_MODEL": "custom-embedding",
            }
        )

        self.assertEqual(settings.api_key, "secret")
        self.assertEqual(settings.generation_model, "custom-generation")
        self.assertEqual(settings.embedding_model, "custom-embedding")


if __name__ == "__main__":
    unittest.main()
