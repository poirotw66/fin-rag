from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.agent import FinRagAgent
from fin_rag.cli import configure_utf8_stdio
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient
from fin_rag.retrieve import Retriever


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
    print(result.answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
