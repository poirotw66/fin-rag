import asyncio
import importlib
import unittest
from types import SimpleNamespace

import httpx


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
            },
        )

if __name__ == "__main__":
    unittest.main()
