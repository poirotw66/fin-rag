from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .agent import REFUSAL_POLICY, FinRagAgent

_LEGAL_DISCLAIMER = REFUSAL_POLICY.rpartition("且")[2].rstrip("。")


@dataclass(frozen=True)
class GoldenCase:
    id: str
    track: str
    question: str
    expected_refs: list[tuple[str, str]]
    expect_refusal: bool


@dataclass(frozen=True)
class ScenarioCase:
    id: str
    persona: str
    scenario_type: str
    question: str
    expect_refusal: bool
    required_refs: list[tuple[str, str]]
    any_of_refs: list[tuple[str, str]]
    forbidden_refs: list[tuple[str, str]]


def load_golden(path: str | Path) -> list[GoldenCase]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [
        GoldenCase(
            id=item["id"],
            track=item["track"],
            question=item["question"],
            expected_refs=[tuple(ref) for ref in item["expected_refs"]],
            expect_refusal=_require_bool(item["expect_refusal"], field="expect_refusal"),
        )
        for item in data
    ]


def load_scenarios(path: str | Path) -> list[ScenarioCase]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [
        ScenarioCase(
            id=item["id"],
            persona=item["persona"],
            scenario_type=item["scenario_type"],
            question=item["question"],
            expect_refusal=_require_bool(item["expect_refusal"], field="expect_refusal"),
            required_refs=[tuple(ref) for ref in item.get("required_refs", [])],
            any_of_refs=[tuple(ref) for ref in item.get("any_of_refs", [])],
            forbidden_refs=[tuple(ref) for ref in item.get("forbidden_refs", [])],
        )
        for item in data
    ]


def run_eval(
    agent: FinRagAgent,
    cases: list[GoldenCase],
    *,
    max_workers: int = 1,
) -> dict[str, Any]:
    if max_workers <= 1:
        results = [_evaluate_case(agent, case) for case in cases]
    else:
        results = _evaluate_cases_parallel(agent, cases, max_workers=max_workers)
    total = len(results)
    return {
        "total": total,
        "citation_hit_rate": _rate(item["citation_hit"] for item in results),
        "refusal_accuracy": _rate(item["refusal_correct"] for item in results),
        "expected_refs_retrieved_rate": _rate(item["expected_refs_retrieved"] for item in results),
        "results": results,
    }


def run_scenarios(
    agent: FinRagAgent,
    cases: list[ScenarioCase],
    *,
    max_workers: int = 1,
) -> dict[str, Any]:
    if max_workers <= 1:
        results = [_evaluate_scenario_case(agent, case) for case in cases]
    else:
        results = _evaluate_scenarios_parallel(agent, cases, max_workers=max_workers)
    return {
        "total": len(results),
        "citation_hit_rate": _rate(item["citation_hit"] for item in results),
        "refusal_accuracy": _rate(item["refusal_correct"] for item in results),
        "required_refs_hit_rate": _rate(item["required_refs_hit"] for item in results),
        "any_of_refs_hit_rate": _rate(item["any_of_refs_hit"] for item in results),
        "forbidden_refs_clear_rate": _rate(
            not item["forbidden_refs_present"] for item in results
        ),
        "disclaimer_presence_rate": _rate(item["disclaimer_present"] for item in results),
        "critical_failures": sum(1 for item in results if item["critical_failure"]),
        "results": results,
    }


def _evaluate_case(agent: FinRagAgent, case: GoldenCase) -> dict[str, Any]:
    started = time.perf_counter()
    result = agent.answer(case.question)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    retrieved_refs = {(item.chunk.doc_id, item.chunk.article) for item in result.retrieved}
    expected_refs = set(case.expected_refs)
    expected_hit = expected_refs.issubset(retrieved_refs) if expected_refs else True
    citation_ok = result.citation_hit if not case.expect_refusal else True
    refusal_ok = result.refused == case.expect_refusal
    return {
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


def _evaluate_scenario_case(agent: FinRagAgent, case: ScenarioCase) -> dict[str, Any]:
    started = time.perf_counter()
    result = agent.answer(case.question)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    retrieved_refs = {(item.chunk.doc_id, item.chunk.article) for item in result.retrieved}
    required_refs_hit = set(case.required_refs).issubset(retrieved_refs) if case.required_refs else True
    any_of_refs_hit = bool(retrieved_refs.intersection(case.any_of_refs)) if case.any_of_refs else True
    forbidden_refs_present = [ref for ref in case.forbidden_refs if ref in retrieved_refs]
    disclaimer_present = _LEGAL_DISCLAIMER in result.answer
    refusal_correct = result.refused == case.expect_refusal
    corpus_boundary_case = case.scenario_type == "out_of_scope" and not case.expect_refusal
    citation_ok = (
        True
        if corpus_boundary_case
        else (result.citation_hit if not case.expect_refusal else True)
    )
    critical_failure = (
        not refusal_correct
        or not citation_ok
        or not required_refs_hit
        or not any_of_refs_hit
        or bool(forbidden_refs_present)
        or not disclaimer_present
    )
    return {
        "id": case.id,
        "persona": case.persona,
        "scenario_type": case.scenario_type,
        "question": case.question,
        "refused": result.refused,
        "expected_refusal": case.expect_refusal,
        "refusal_correct": refusal_correct,
        "citation_hit": citation_ok,
        "required_refs_hit": required_refs_hit,
        "any_of_refs_hit": any_of_refs_hit,
        "forbidden_refs_present": forbidden_refs_present,
        "disclaimer_present": disclaimer_present,
        "critical_failure": critical_failure,
        "latency_ms": latency_ms,
        "answer": result.answer,
    }


def _evaluate_cases_parallel(
    agent: FinRagAgent,
    cases: list[GoldenCase],
    *,
    max_workers: int,
) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any] | None] = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_evaluate_case, agent, case): index
            for index, case in enumerate(cases)
        }
        for future in futures:
            index = futures[future]
            ordered[index] = future.result()
    return [item for item in ordered if item is not None]


def _evaluate_scenarios_parallel(
    agent: FinRagAgent,
    cases: list[ScenarioCase],
    *,
    max_workers: int,
) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any] | None] = [None] * len(cases)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_evaluate_scenario_case, agent, case): index
            for index, case in enumerate(cases)
        }
        for future in futures:
            index = futures[future]
            ordered[index] = future.result()
    return [item for item in ordered if item is not None]


def _rate(values) -> float:
    items = list(values)
    if not items:
        return 0.0
    return round(sum(1 for item in items if item) / len(items), 4)


def _require_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{field} must be a boolean")
    return value
