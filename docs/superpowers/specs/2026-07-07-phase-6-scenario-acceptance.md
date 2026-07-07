# Phase 6 Scenario Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a scenario-based acceptance eval track that measures whether Fin RAG is usable in realistic workplace regulatory questions, while keeping Phase 5 golden regression unchanged.

**Architecture:** Reuse the existing `fin_rag.eval` pattern, but add a scenario-specific schema and runner so `eval/golden.yaml` stays stable. Auto-scored fields live in code and JSON reports; subjective rubric fields live in a separate review template file that can be filled by a human or an LLM reviewer later.

**Tech Stack:** Python 3.10+, `yaml`, existing `FinRagAgent`, existing retrieval/agent stack, `unittest`, JSON reports in `eval/`

---

## File map

| File | Action | Responsibility |
|------|--------|----------------|
| `src/fin_rag/eval.py` | Modify | Add scenario dataclass, YAML loader, auto-eval logic, and report aggregation |
| `eval/run.py` | Keep | Golden regression runner remains unchanged |
| `eval/run_scenarios.py` | Create | CLI entrypoint for scenario acceptance run |
| `eval/scenarios.yaml` | Create | 20 real-world scenario cases |
| `eval/scenario_review.template.yaml` | Create | Human/LLM rubric template for R1/R3/R4 |
| `tests/test_eval.py` | Modify | Unit tests for new loader/report logic |
| `README.md` | Modify | Add one-line Phase 6 evaluation track note |
| `readme-tw.md` | Modify | Add one-line Phase 6 evaluation track note in Traditional Chinese |

---

### Task 1: Add scenario schema and loader

**Files:**
- Modify: `src/fin_rag/eval.py`
- Modify: `tests/test_eval.py`

- [ ] **Step 1: Write the failing loader tests**

Add tests like:

```python
def test_load_scenarios_reads_yaml_fields(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "scenarios.yaml"
        path.write_text(
            "- id: SC01\n"
            "  persona: compliance\n"
            "  scenario_type: colloquial\n"
            "  question: 我們銀行想放款給董事的配偶，授信上有什麼限制？\n"
            "  expect_refusal: false\n"
            "  any_of_refs:\n"
            "    - [bank-act, 第 32 條]\n"
            "  forbidden_refs:\n"
            "    - [insurance-act, 第 137 條]\n"
            "  must_acknowledge_subset: true\n",
            encoding="utf-8",
        )

        cases = load_scenarios(path)

    self.assertEqual(cases[0].id, "SC01")
    self.assertEqual(cases[0].persona, "compliance")
    self.assertEqual(cases[0].any_of_refs, [("bank-act", "第 32 條")])
    self.assertEqual(cases[0].forbidden_refs, [("insurance-act", "第 137 條")])
    self.assertTrue(cases[0].must_acknowledge_subset)


def test_load_scenarios_defaults_optional_fields(self):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "scenarios.yaml"
        path.write_text(
            "- id: SC02\n"
            "  persona: general\n"
            "  scenario_type: out_of_scope\n"
            "  question: 信用卡循環利率上限是多少？\n"
            "  expect_refusal: false\n",
            encoding="utf-8",
        )

        cases = load_scenarios(path)

    self.assertEqual(cases[0].required_refs, [])
    self.assertEqual(cases[0].any_of_refs, [])
    self.assertEqual(cases[0].forbidden_refs, [])
    self.assertFalse(cases[0].must_state_out_of_corpus)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_eval.EvalTests -v`

Expected: `ImportError` or `AttributeError` because `load_scenarios` does not exist yet.

- [ ] **Step 3: Add minimal scenario dataclass and loader**

In `src/fin_rag/eval.py`, add:

```python
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
    rubric_notes: str
    must_acknowledge_subset: bool
    must_state_out_of_corpus: bool


def load_scenarios(path: str | Path) -> list[ScenarioCase]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return [
        ScenarioCase(
            id=item["id"],
            persona=item["persona"],
            scenario_type=item["scenario_type"],
            question=item["question"],
            expect_refusal=bool(item["expect_refusal"]),
            required_refs=[tuple(ref) for ref in item.get("required_refs", [])],
            any_of_refs=[tuple(ref) for ref in item.get("any_of_refs", [])],
            forbidden_refs=[tuple(ref) for ref in item.get("forbidden_refs", [])],
            rubric_notes=item.get("rubric_notes", ""),
            must_acknowledge_subset=bool(item.get("must_acknowledge_subset", False)),
            must_state_out_of_corpus=bool(item.get("must_state_out_of_corpus", False)),
        )
        for item in data
    ]
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m unittest tests.test_eval.EvalTests -v`

Expected: all loader tests PASS.

---

### Task 2: Add scenario auto-eval and report aggregation

**Files:**
- Modify: `src/fin_rag/eval.py`
- Modify: `tests/test_eval.py`

- [ ] **Step 1: Write the failing auto-eval tests**

Add tests like:

```python
def test_run_scenarios_reports_any_of_and_forbidden_refs(self):
    class FakeChunk:
        def __init__(self, doc_id: str, article: str):
            self.doc_id = doc_id
            self.article = article

    class FakeHit:
        def __init__(self, doc_id: str, article: str):
            self.chunk = FakeChunk(doc_id, article)

    class FakeAgent:
        def answer(self, question: str) -> AgentResult:
            return AgentResult(
                answer="依 bank-act 第 33 條，本回答不構成法律意見。",
                refused=False,
                citation_hit=True,
                retrieved=[FakeHit("bank-act", "第 33 條")],
            )

    cases = [
        ScenarioCase(
            id="SC10",
            persona="compliance",
            scenario_type="subset_boundary",
            question="銀行對同一關係人授信總額有沒有固定百分比上限？",
            expect_refusal=False,
            required_refs=[],
            any_of_refs=[("bank-act", "第 33 條")],
            forbidden_refs=[("insurance-act", "第 137 條")],
            rubric_notes="",
            must_acknowledge_subset=True,
            must_state_out_of_corpus=False,
        )
    ]

    report = run_scenarios(FakeAgent(), cases)

    self.assertEqual(report["total"], 1)
    self.assertEqual(report["auto"]["any_of_refs_hit_rate"], 1.0)
    self.assertEqual(report["auto"]["critical_failure_count"], 0)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m unittest tests.test_eval.RunEvalTests -v`

Expected: failure because `run_scenarios` does not exist yet.

- [ ] **Step 3: Implement minimal scenario eval**

In `src/fin_rag/eval.py`, add:

```python
def run_scenarios(agent: FinRagAgent, cases: list[ScenarioCase]) -> dict[str, Any]:
    results = [_evaluate_scenario(agent, case) for case in cases]
    latencies = [item["latency_ms"] for item in results]
    return {
        "total": len(results),
        "auto": {
            "refusal_accuracy": _rate(item["refusal_correct"] for item in results),
            "any_of_refs_hit_rate": _rate(item["any_of_refs_hit"] for item in results if not item["expected_refusal"]),
            "citation_hit_rate": _rate(item["citation_hit"] for item in results if not item["expected_refusal"]),
            "disclaimer_present_rate": _rate(item["disclaimer_present"] for item in results),
            "critical_failure_count": sum(1 for item in results if item["critical_failure"]),
        },
        "latency_ms_p95": _p95(latencies),
        "results": results,
    }
```

And per-case evaluation:

```python
def _evaluate_scenario(agent: FinRagAgent, case: ScenarioCase) -> dict[str, Any]:
    started = time.perf_counter()
    result = agent.answer(case.question)
    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    retrieved_refs = {(item.chunk.doc_id, item.chunk.article) for item in result.retrieved}
    required_hit = set(case.required_refs).issubset(retrieved_refs) if case.required_refs else True
    any_of_hit = bool(set(case.any_of_refs) & retrieved_refs) if case.any_of_refs else True
    forbidden_hit = bool(set(case.forbidden_refs) & retrieved_refs)
    disclaimer_present = "不構成法律意見" in result.answer
    refusal_correct = result.refused == case.expect_refusal
    fabricated_percentage = case.id == "SC10" and "%" in result.answer
    critical_failure = forbidden_hit or fabricated_percentage or (case.expect_refusal and not result.refused)
    return {
        "id": case.id,
        "persona": case.persona,
        "scenario_type": case.scenario_type,
        "question": case.question,
        "refused": result.refused,
        "expected_refusal": case.expect_refusal,
        "refusal_correct": refusal_correct,
        "citation_hit": result.citation_hit if not case.expect_refusal else True,
        "required_refs_hit": required_hit,
        "any_of_refs_hit": any_of_hit,
        "forbidden_refs_hit": forbidden_hit,
        "disclaimer_present": disclaimer_present,
        "critical_failure": critical_failure,
        "latency_ms": latency_ms,
        "answer": result.answer,
    }
```

- [ ] **Step 4: Add a tiny percentile helper**

In `src/fin_rag/eval.py`, add:

```python
def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(len(ordered) * 0.95) - 1))
    return ordered[index]
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m unittest tests.test_eval.RunEvalTests -v`

Expected: new scenario eval tests PASS.

---

### Task 3: Add scenario CLI runner

**Files:**
- Create: `eval/run_scenarios.py`
- Modify: `tests/test_eval.py`

- [ ] **Step 1: Write the failing smoke test**

Add a test like:

```python
def test_run_scenarios_report_has_auto_and_results(self):
    class FakeChunk:
        def __init__(self, doc_id: str, article: str):
            self.doc_id = doc_id
            self.article = article

    class FakeHit:
        def __init__(self, doc_id: str, article: str):
            self.chunk = FakeChunk(doc_id, article)

    class FakeAgent:
        def answer(self, question: str) -> AgentResult:
            return AgentResult(
                answer="依 insurance-act 第 137 條，本回答不構成法律意見。",
                refused=False,
                citation_hit=True,
                retrieved=[FakeHit("insurance-act", "第 137 條")],
            )

    report = run_scenarios(FakeAgent(), [
        ScenarioCase(
            id="SC02",
            persona="insurance",
            scenario_type="colloquial",
            question="想新設一家保險公司，一開始要過哪些主管機關關卡？",
            expect_refusal=False,
            required_refs=[],
            any_of_refs=[("insurance-act", "第 137 條")],
            forbidden_refs=[],
            rubric_notes="",
            must_acknowledge_subset=False,
            must_state_out_of_corpus=False,
        )
    ])

    self.assertIn("auto", report)
    self.assertEqual(report["results"][0]["id"], "SC02")
```

- [ ] **Step 2: Create the runner script**

Add `eval/run_scenarios.py`:

```python
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
from fin_rag.eval import load_scenarios, run_scenarios
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
    report = run_scenarios(agent, load_scenarios(ROOT / "eval" / "scenarios.yaml"))
    out_path = ROOT / "eval" / "last_scenarios_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "results"}, ensure_ascii=False, indent=2))
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run the eval tests**

Run: `python -m unittest tests.test_eval -v`

Expected: all `test_eval` tests PASS.

---

### Task 4: Author the scenario dataset and review template

**Files:**
- Create: `eval/scenarios.yaml`
- Create: `eval/scenario_review.template.yaml`
- Test: `tests/test_eval.py`

- [ ] **Step 1: Create `eval/scenarios.yaml` with 20 scenarios**

Start the file like:

```yaml
- id: SC01
  persona: compliance
  scenario_type: colloquial
  question: 我們銀行想放款給董事的配偶，授信上有什麼限制？
  expect_refusal: false
  any_of_refs:
    - [bank-act, 第 32 條]
    - [bank-act, 第 33 條]
  rubric_notes: 應點出利害關係授信限制，不要只重複條文標題。

- id: SC02
  persona: insurance
  scenario_type: colloquial
  question: 想新設一家保險公司，一開始要過哪些主管機關關卡？
  expect_refusal: false
  any_of_refs:
    - [insurance-act, 第 137 條]
  rubric_notes: 應先回答需經主管機關許可並完成設立登記、保證金與營業執照。

- id: SC03
  persona: compliance
  scenario_type: colloquial
  question: 新客戶 onboarding 做 KYC，實務上至少要做哪些事？
  expect_refusal: false
  any_of_refs:
    - [aml-finst, 第 3 條]
    - [aml-finst, 第 7 條]
  rubric_notes: 應回答辨識、驗證、實質受益人與目的性質。
```

Continue until `SC20`, following the approved spec inventory.

- [ ] **Step 2: Create review template**

Create `eval/scenario_review.template.yaml` like:

```yaml
- id: SC01
  r1_scope: null
  r3_usefulness: null
  r4_epistemic: null
  weighted_pass: null
  reviewer_notes: ""

- id: SC02
  r1_scope: null
  r3_usefulness: null
  r4_epistemic: null
  weighted_pass: null
  reviewer_notes: ""
```

Include all 20 scenario ids so the review file is ready to fill.

- [ ] **Step 3: Add a dataset sanity test**

Add a test like:

```python
def test_scenarios_file_contains_20_cases(self):
    cases = load_scenarios(Path("eval/scenarios.yaml"))
    self.assertEqual(len(cases), 20)
    self.assertEqual(cases[0].id, "SC01")
    self.assertEqual(cases[-1].id, "SC20")
```

- [ ] **Step 4: Run the dataset test**

Run: `python -m unittest tests.test_eval.EvalTests -v`

Expected: PASS with 20 scenarios loaded.

---

### Task 5: Add docs and verification flow

**Files:**
- Modify: `README.md`
- Modify: `readme-tw.md`

- [ ] **Step 1: Add one roadmap line to `README.md`**

Add near the current roadmap:

```markdown
- **Phase 6 (planned)**: Scenario-based acceptance eval for realistic workplace regulatory questions, separate from golden regression
```

- [ ] **Step 2: Add one roadmap line to `readme-tw.md`**

Add the Traditional Chinese version:

```markdown
- **Phase 6（規劃中）**：新增真實工作情境驗收評估，與 golden regression 分開追蹤
```

- [ ] **Step 3: Run targeted tests**

Run: `python -m unittest tests.test_eval -v`

Expected: PASS.

---

### Task 6: End-to-end scenario run and baseline freeze

**Files:**
- Create: `eval/baseline-phase6-scenarios.json`
- Regenerate: `eval/last_scenarios_report.json`

- [ ] **Step 1: Run golden regression first**

Run: `FIN_RAG_RETRIEVAL_MODE=hybrid python eval/run.py`

Expected: metrics remain at or above Phase 5 baseline.

- [ ] **Step 2: Run the scenario eval**

Run: `FIN_RAG_RETRIEVAL_MODE=hybrid python eval/run_scenarios.py`

Expected summary shape:

```json
{
  "total": 20,
  "auto": {
    "refusal_accuracy": 1.0,
    "any_of_refs_hit_rate": 0.85,
    "citation_hit_rate": 0.9,
    "disclaimer_present_rate": 1.0,
    "critical_failure_count": 0
  }
}
```

- [ ] **Step 3: Freeze the baseline**

Run: `cp eval/last_scenarios_report.json eval/baseline-phase6-scenarios.json`

- [ ] **Step 4: Run repo smoke checks**

Run: `python scripts/spot_check_corpus.py`

Expected: `OK: spot-check passed`

Run: `python run_tests.py`

Expected: all tests pass, with existing integration skips only.

- [ ] **Step 5: Commit when the user asks**

```bash
git add src/fin_rag/eval.py eval/run_scenarios.py eval/scenarios.yaml eval/scenario_review.template.yaml eval/baseline-phase6-scenarios.json README.md readme-tw.md tests/test_eval.py
git commit -m "feat(eval): add scenario-based acceptance evaluation"
```

---

## Verification checklist

| Check | Command / file |
|-------|----------------|
| 20 scenario cases | `python -m unittest tests.test_eval.EvalTests.test_scenarios_file_contains_20_cases -v` |
| Golden unchanged | `FIN_RAG_RETRIEVAL_MODE=hybrid python eval/run.py` |
| Scenario report emitted | `FIN_RAG_RETRIEVAL_MODE=hybrid python eval/run_scenarios.py` |
| Critical failures zero | `eval/last_scenarios_report.json` |
| Spot-check | `python scripts/spot_check_corpus.py` |
| Tests | `python run_tests.py` |

## Spec coverage self-review

| Spec requirement | Task |
|------------------|------|
| Separate scenario track from golden | Task 1–3 |
| 20 realistic scenarios | Task 4 |
| Auto metrics for objective checks | Task 2–3 |
| Human/LLM rubric template | Task 4 |
| Pass gates and baseline freeze | Task 6 |
| README messaging | Task 5 |
