from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class GeminiError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeminiClient:
    api_key: str
    generation_model: str
    embedding_model: str

    def embed(self, text: str) -> list[float]:
        sdk_client = self._sdk_client()
        if sdk_client is not None:
            response = sdk_client.models.embed_content(model=self.embedding_model, contents=text)
            return [float(value) for value in response.embeddings[0].values]
        payload = {
            "model": f"models/{self.embedding_model}",
            "content": {"parts": [{"text": text}]},
        }
        data = self._post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.embedding_model}:embedContent?key={self.api_key}",
            payload,
        )
        values = data.get("embedding", {}).get("values")
        if not isinstance(values, list):
            raise GeminiError(f"Unexpected embedding response: {data}")
        return [float(value) for value in values]

    def generate(self, prompt: str) -> str:
        sdk_client = self._sdk_client()
        if sdk_client is not None:
            response = sdk_client.models.generate_content(
                model=self.generation_model,
                contents=prompt,
                config={"temperature": 0},
            )
            return (response.text or "").strip()
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0},
        }
        data = self._post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.generation_model}:generateContent?key={self.api_key}",
            payload,
        )
        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError) as exc:
            raise GeminiError(f"Unexpected generation response: {data}") from exc
        return "\n".join(part.get("text", "") for part in parts).strip()

    def _post(self, url: str, payload: dict) -> dict:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GeminiError(f"Gemini HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise GeminiError(f"Gemini request failed: {exc}") from exc

    def _sdk_client(self) -> Any | None:
        try:
            from google import genai
        except Exception:
            return None
        return genai.Client(api_key=self.api_key)
