from __future__ import annotations

from .gemini import GeminiClient
from .types import RetrievedChunk
from .vector_store import read_index, search


class Retriever:
    def __init__(self, *, client: GeminiClient, index_path: str, top_k: int = 8):
        self.client = client
        self.index_path = index_path
        self.top_k = top_k

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        records = read_index(self.index_path)
        query_embedding = self.client.embed(question)
        return search(records, query_embedding, self.top_k)

