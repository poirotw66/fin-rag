from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    generation_model: str
    embedding_model: str
    retrieval_mode: str
    vector_backend: str

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "Settings":
        source = dict(os.environ if env is None else env)
        if env is None:
            source.update(_read_dotenv(Path(".env")))
        retrieval_mode = source.get("FIN_RAG_RETRIEVAL_MODE", "hybrid").strip().lower()
        if retrieval_mode not in {"hybrid", "embedding"}:
            raise ValueError("FIN_RAG_RETRIEVAL_MODE must be 'hybrid' or 'embedding'")
        vector_backend = source.get("FIN_RAG_VECTOR_BACKEND", "auto").strip().lower()
        if vector_backend not in {"auto", "faiss", "jsonl"}:
            raise ValueError("FIN_RAG_VECTOR_BACKEND must be 'auto', 'faiss', or 'jsonl'")
        return cls(
            api_key=source.get("GEMINI_API_KEY"),
            generation_model=source.get("FIN_RAG_GENERATION_MODEL", "gemini-2.5-flash"),
            embedding_model=source.get("FIN_RAG_EMBEDDING_MODEL", "gemini-embedding-2"),
            retrieval_mode=retrieval_mode,
            vector_backend=vector_backend,
        )


def _read_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
