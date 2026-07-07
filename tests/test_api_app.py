import asyncio
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.agent import AgentResult
from fin_rag.types import Chunk, RetrievedChunk


def _retrieved_chunk(
    *,
    doc_id: str,
    article: str,
    title: str,
    text: str,
    score: float = 0.9,
) -> RetrievedChunk:
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


class ApiAppTests(unittest.TestCase):
    def _request(self, method: str, path: str, *, app, json=None):
        async def make_request():
            transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, json=json)

        return asyncio.run(make_request())

    def test_api_app_module_imports_without_test_path_hacks(self):
        module = importlib.import_module("apps.api.app")

        self.assertTrue(callable(module.create_app))

    def test_health_endpoint_returns_ok(self):
        create_app = importlib.import_module("apps.api.app").create_app
        response = self._request("GET", "/api/health", app=create_app())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_ask_endpoint_returns_agent_payload(self):
        app_module = importlib.import_module("apps.api.app")
        deps_module = importlib.import_module("apps.api.deps")
        app = app_module.create_app()

        class StubAgent:
            def answer(self, question):
                return SimpleNamespace(
                    answer="Stub answer",
                    refused=False,
                    citation_hit=False,
                    retrieved=[],
                    refusal_reason=None,
                    retrieval_confidence=None,
                    retrieval_round=0,
                    generation_attempts=0,
                )

        app.dependency_overrides[deps_module.get_agent] = lambda: StubAgent()

        try:
            response = self._request(
                "POST",
                "/api/ask",
                app=app,
                json={"question": "What is a CDD rule?"},
            )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "question": "What is a CDD rule?",
                "answer": "Stub answer",
                "refused": False,
                "citation_hit": False,
                "citations": [],
                "retrieved": [],
                "refusal_reason": None,
                "retrieval_confidence": None,
                "retrieval_round": 0,
                "generation_attempts": 0,
            },
        )

    def test_ask_returns_503_when_api_key_missing(self):
        app = importlib.import_module("apps.api.app").create_app()

        with patch(
            "apps.api.deps.build_agent",
            side_effect=RuntimeError("GEMINI_API_KEY is required"),
        ):
            response = self._request(
                "POST",
                "/api/ask",
                app=app,
                json={"question": "What is a CDD rule?"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "GEMINI_API_KEY is required"})

    def test_ask_returns_503_when_index_missing(self):
        app = importlib.import_module("apps.api.app").create_app()

        with patch(
            "apps.api.deps.build_agent",
            side_effect=RuntimeError("corpus/index.jsonl is required"),
        ):
            response = self._request(
                "POST",
                "/api/ask",
                app=app,
                json={"question": "What is a CDD rule?"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "corpus/index.jsonl is required"})

    def test_ask_endpoint_returns_citations_and_retrieved_chunks(self):
        app_module = importlib.import_module("apps.api.app")
        deps_module = importlib.import_module("apps.api.deps")
        app = app_module.create_app()

        class StubAgent:
            def answer(self, question):
                return AgentResult(
                    answer="Stub answer",
                    refused=False,
                    citation_hit=True,
                    retrieved=[
                        _retrieved_chunk(
                            doc_id="aml-finst",
                            article="第 7 條",
                            title="金融機構防制洗錢辦法",
                            text="金融機構應進行客戶身分確認。",
                        )
                    ],
                )

        app.dependency_overrides[deps_module.get_agent] = lambda: StubAgent()

        try:
            response = self._request(
                "POST",
                "/api/ask",
                app=app,
                json={"question": "What is a CDD rule?"},
            )
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["citations"][0]["doc_id"], "aml-finst")
        self.assertEqual(body["retrieved"][0]["score"], 0.9)

if __name__ == "__main__":
    unittest.main()
