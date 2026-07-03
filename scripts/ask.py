from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.agent import FinRagAgent
from fin_rag.cli import configure_utf8_stdio
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient
from fin_rag.types import RetrievedChunk
from fin_rag.retrieve import Retriever


def format_result(result) -> str:
    sections = [
        "Answer",
        result.answer,
        "",
        f"Refused: {'yes' if result.refused else 'no'}",
        "",
        "Citations",
        _format_citations(result.retrieved),
        "",
        "Retrieved Chunks",
        _format_retrieved_chunks(result.retrieved),
    ]
    return "\n".join(sections)


def _format_citations(retrieved: list[RetrievedChunk]) -> str:
    if not retrieved:
        return "- none"
    lines: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    for item in retrieved:
        citation = (item.chunk.doc_id, item.chunk.article, item.chunk.title)
        if citation in seen:
            continue
        seen.add(citation)
        lines.append(f"- {item.chunk.doc_id} / {item.chunk.article} / {item.chunk.title}")
    return "\n".join(lines)


def _format_retrieved_chunks(retrieved: list[RetrievedChunk]) -> str:
    if not retrieved:
        return "- none"
    lines: list[str] = []
    for index, item in enumerate(retrieved, 1):
        snippet = _summarize_text(item.chunk.text)
        lines.append(f"[{index}] {item.chunk.doc_id} / {item.chunk.article} / score={item.score:.2f}")
        lines.append(f"    {snippet}")
    return "\n".join(lines)


def _summarize_text(text: str, limit: int = 90) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def main() -> int:
    configure_utf8_stdio()
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        print("usage: python scripts/ask.py <question>", file=sys.stderr)
        return 1
    settings = Settings.from_env()
    if not settings.api_key:
        print("GEMINI_API_KEY is required in .env", file=sys.stderr)
        return 1
    client = GeminiClient(settings.api_key, settings.generation_model, settings.embedding_model)
    retriever = Retriever(client=client, index_path=str(ROOT / "corpus" / "index.jsonl"))
    agent = FinRagAgent(client=client, retrieve=retriever.retrieve)
    result = agent.answer(question)
    print(format_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
