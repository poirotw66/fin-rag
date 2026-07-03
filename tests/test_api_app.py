import asyncio
import importlib
import unittest

import httpx


class ApiAppTests(unittest.TestCase):
    def test_api_app_module_imports_without_test_path_hacks(self):
        module = importlib.import_module("apps.api.app")

        self.assertTrue(callable(module.create_app))

    def test_health_endpoint_returns_ok(self):
        create_app = importlib.import_module("apps.api.app").create_app

        async def get_response():
            transport = httpx.ASGITransport(app=create_app())
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.get("/api/health")

        response = asyncio.run(get_response())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
