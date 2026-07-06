from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.agent import FinRagAgent
from fin_rag.cli import configure_utf8_stdio
from fin_rag.config import Settings
from fin_rag.eval import load_golden, run_eval
from fin_rag.gemini import GeminiClient
from fin_rag.retrieve import Retriever


def main() -> int:
    configure_utf8_stdio()
    settings = Settings.from_env()
    if not settings.api_key:
        print("GEMINI_API_KEY is required in .env", file=sys.stderr)
        return 1
    client = GeminiClient(settings.api_key, settings.generation_model, settings.embedding_model)
    retriever = Retriever(
        client=client,
        index_path=str(ROOT / "corpus" / "index.jsonl"),
        retrieval_mode=settings.retrieval_mode,
        vector_backend=settings.vector_backend,
    )
    agent = FinRagAgent(
        client=client,
        retrieve=retriever.retrieve,
        retrieve_queries=retriever.retrieve_queries,
        min_retrieval_score=settings.min_retrieval_score,
        max_retrieval_rounds=settings.max_retrieval_rounds,
    )
    report = run_eval(
        agent,
        load_golden(ROOT / "eval" / "golden.yaml"),
        max_workers=max(1, int(os.environ.get("FIN_RAG_EVAL_WORKERS", "5"))),
    )
    out_path = ROOT / "eval" / "last_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, ensure_ascii=False, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
