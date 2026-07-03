from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .agent import FinRagAgent


@dataclass(frozen=True)
class GoldenCase:
    id: str
    track: str
    question: str
    expected_refs: list[tuple[str, str]]
    expect_refusal: bool


def load_golden(path: str | Path) -> list[GoldenCase]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        GoldenCase(
            id=item["id"],
            track=item["track"],
            question=item["question"],
            expected_refs=[tuple(ref) for ref in item["expected_refs"]],
            expect_refusal=bool(item["expect_refusal"]),
        )
        for item in data
    ]


def run_eval(agent: FinRagAgent, cases: list[GoldenCase]) -> dict[str, Any]:
    results = []
    for case in cases:
        started = time.perf_counter()
        result = agent.answer(case.question)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        retrieved_refs = {(item.chunk.doc_id, item.chunk.article) for item in result.retrieved}
        expected_refs = set(case.expected_refs)
        expected_hit = expected_refs.issubset(retrieved_refs) if expected_refs else True
        citation_ok = result.citation_hit if not case.expect_refusal else True
        refusal_ok = result.refused == case.expect_refusal
        results.append(
            {
                "id": case.id,
                "track": case.track,
                "question": case.question,
                "refused": result.refused,
                "expected_refusal": case.expect_refusal,
                "refusal_correct": refusal_ok,
                "citation_hit": citation_ok,
                "expected_refs_retrieved": expected_hit,
                "latency_ms": latency_ms,
                "answer": result.answer,
            }
        )
    total = len(results)
    return {
        "total": total,
        "citation_hit_rate": _rate(item["citation_hit"] for item in results),
        "refusal_accuracy": _rate(item["refusal_correct"] for item in results),
        "expected_refs_retrieved_rate": _rate(item["expected_refs_retrieved"] for item in results),
        "results": results,
    }


def _rate(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(1 for item in items if item) / len(items), 4)

