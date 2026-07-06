from __future__ import annotations

from pathlib import Path

from fin_rag.agent import FinRagAgent
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient
from fin_rag.faiss_store import faiss_paths_for
from fin_rag.retrieve import Retriever

ROOT = Path(__file__).resolve().parents[2]


def build_agent() -> FinRagAgent:
    settings = Settings.from_env()
    if not settings.api_key:
        raise RuntimeError("GEMINI_API_KEY is required")

    index_path = ROOT / "corpus" / "index.jsonl"
    faiss_path, meta_path = faiss_paths_for(index_path)
    if not index_path.exists() and not (faiss_path.exists() and meta_path.exists()):
        raise RuntimeError("corpus/index.jsonl or corpus/index.faiss is required")

    client = GeminiClient(
        api_key=settings.api_key,
        generation_model=settings.generation_model,
        embedding_model=settings.embedding_model,
    )
    retriever = Retriever(
        client=client,
        index_path=str(index_path),
        retrieval_mode=settings.retrieval_mode,
        vector_backend=settings.vector_backend,
    )
    return FinRagAgent(
        client=client,
        retrieve=retriever.retrieve,
        retrieve_queries=retriever.retrieve_queries,
    )
