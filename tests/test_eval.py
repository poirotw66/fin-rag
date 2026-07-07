import contextlib
import importlib.util
import io
import json
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import ANY

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fin_rag.agent import AgentResult
from fin_rag.eval import GoldenCase, ScenarioCase, load_golden, load_scenarios, run_eval, run_scenarios
from fin_rag.types import Chunk, RetrievedChunk


class EvalTests(unittest.TestCase):
    def test_load_golden_reads_yaml(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "golden.yaml"
            path.write_text(
                "- id: C1\n"
                "  track: C\n"
                "  question: 國泰投信會被金管會罰多少錢？\n"
                "  expected_refs: []\n"
                "  expect_refusal: true\n",
                encoding="utf-8",
            )

            cases = load_golden(path)

        self.assertEqual(cases[0].id, "C1")
        self.assertTrue(cases[0].expect_refusal)

    def test_load_golden_reads_json_compatibility_input(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "golden.yaml"
            path.write_text(
                '[{"id":"A1","track":"A","question":"什麼是風險基礎方法？","expected_refs":[["aml-finst","第 2 條"]],"expect_refusal":false}]',
                encoding="utf-8",
            )

            cases = load_golden(path)

        self.assertEqual(cases[0].id, "A1")
        self.assertEqual(cases[0].expected_refs, [("aml-finst", "第 2 條")])
        self.assertFalse(cases[0].expect_refusal)

    def test_load_golden_rejects_string_expect_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "golden.yaml"
            path.write_text(
                "- id: C2\n"
                "  track: C\n"
                "  question: 國泰投信會被金管會罰多少錢？\n"
                "  expected_refs: []\n"
                '  expect_refusal: "false"\n',
                encoding="utf-8",
            )

            with self.assertRaises(TypeError):
                load_golden(path)


class LoadScenariosTests(unittest.TestCase):
    def test_load_scenarios_reads_required_fields_and_optional_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scenarios.yaml"
            path.write_text(
                "- id: S1\n"
                "  persona: Compliance officer\n"
                "  scenario_type: grounded\n"
                "  question: Which article applies?\n"
                "  expect_refusal: false\n"
                "  required_refs:\n"
                '    - ["aml-finst", "第 2 條"]\n'
                "  any_of_refs:\n"
                '    - ["bank-act", "第 3 條"]\n'
                '    - ["bank-act", "第 4 條"]\n'
                "  forbidden_refs:\n"
                '    - ["privacy-finance", "第 5 條"]\n',
                encoding="utf-8",
            )

            cases = load_scenarios(path)

        self.assertEqual(cases[0].id, "S1")
        self.assertEqual(cases[0].persona, "Compliance officer")
        self.assertEqual(cases[0].scenario_type, "grounded")
        self.assertEqual(cases[0].question, "Which article applies?")
        self.assertFalse(cases[0].expect_refusal)
        self.assertEqual(cases[0].required_refs, [("aml-finst", "第 2 條")])
        self.assertEqual(
            cases[0].any_of_refs,
            [("bank-act", "第 3 條"), ("bank-act", "第 4 條")],
        )
        self.assertEqual(cases[0].forbidden_refs, [("privacy-finance", "第 5 條")])

    def test_load_scenarios_defaults_missing_optional_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scenarios.yaml"
            path.write_text(
                "- id: S2\n"
                "  persona: Retail investor\n"
                "  scenario_type: refusal\n"
                "  question: Tell me tomorrow's stock price.\n"
                "  expect_refusal: true\n",
                encoding="utf-8",
            )

            cases = load_scenarios(path)

        self.assertEqual(cases[0].required_refs, [])
        self.assertEqual(cases[0].any_of_refs, [])
        self.assertEqual(cases[0].forbidden_refs, [])

    def test_load_scenarios_rejects_string_expect_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "scenarios.yaml"
            path.write_text(
                "- id: S3\n"
                "  persona: Retail investor\n"
                "  scenario_type: refusal\n"
                "  question: Tell me tomorrow's stock price.\n"
                '  expect_refusal: "false"\n',
                encoding="utf-8",
            )

            with self.assertRaises(TypeError):
                load_scenarios(path)

    def test_scenarios_file_contains_20_cases(self) -> None:
        cases = load_scenarios(ROOT / "eval" / "scenarios.yaml")
        self.assertEqual(len(cases), 20)
        self.assertEqual(cases[0].id, "SC01")
        self.assertEqual(cases[-1].id, "SC20")


class RunEvalTests(unittest.TestCase):
    def test_run_eval_preserves_case_order_with_multiple_workers(self) -> None:
        class FakeAgent:
            def answer(self, question: str) -> AgentResult:
                return AgentResult(
                    answer=question,
                    refused=question == "third",
                    citation_hit=True,
                    retrieved=[],
                )

        cases = [
            GoldenCase("A1", "A", "first", [], False),
            GoldenCase("B1", "B", "second", [], False),
            GoldenCase("C1", "C", "third", [], True),
        ]

        report = run_eval(FakeAgent(), cases, max_workers=5)

        self.assertEqual([item["id"] for item in report["results"]], ["A1", "B1", "C1"])
        self.assertEqual(report["total"], 3)
        self.assertEqual(report["refusal_accuracy"], 1.0)


class RunScenariosTests(unittest.TestCase):
    def test_run_scenarios_reports_auto_eval_metrics(self) -> None:
        class FakeAgent:
            def answer(self, question: str) -> AgentResult:
                if question == "grounded":
                    return AgentResult(
                        answer="Answer with disclaimer. 本回答不構成法律意見。",
                        refused=False,
                        citation_hit=True,
                        retrieved=[
                            _retrieved_chunk("aml-finst", "第 2 條"),
                            _retrieved_chunk("bank-act", "第 4 條"),
                        ],
                    )
                return AgentResult(
                    answer="Answer without disclaimer.",
                    refused=False,
                    citation_hit=True,
                    retrieved=[
                        _retrieved_chunk("bank-act", "第 1 條"),
                        _retrieved_chunk("privacy-finance", "第 5 條"),
                    ],
                )

        cases = [
            ScenarioCase(
                id="S1",
                persona="Compliance officer",
                scenario_type="grounded",
                question="grounded",
                expect_refusal=False,
                required_refs=[("aml-finst", "第 2 條")],
                any_of_refs=[("bank-act", "第 3 條"), ("bank-act", "第 4 條")],
                forbidden_refs=[("privacy-finance", "第 5 條")],
            ),
            ScenarioCase(
                id="S2",
                persona="Retail investor",
                scenario_type="grounded",
                question="forbidden",
                expect_refusal=False,
                required_refs=[],
                any_of_refs=[("insurance-act", "第 7 條")],
                forbidden_refs=[("privacy-finance", "第 5 條")],
            ),
        ]

        report = run_scenarios(FakeAgent(), cases)

        self.assertEqual(report["total"], 2)
        self.assertEqual(report["required_refs_hit_rate"], 1.0)
        self.assertEqual(report["any_of_refs_hit_rate"], 0.5)
        self.assertEqual(report["forbidden_refs_clear_rate"], 0.5)
        self.assertEqual(report["disclaimer_presence_rate"], 0.5)
        self.assertEqual(report["critical_failures"], 1)
        self.assertEqual(
            report["results"],
            [
                {
                    "id": "S1",
                    "persona": "Compliance officer",
                    "scenario_type": "grounded",
                    "question": "grounded",
                    "refused": False,
                    "expected_refusal": False,
                    "refusal_correct": True,
                    "citation_hit": True,
                    "required_refs_hit": True,
                    "any_of_refs_hit": True,
                    "forbidden_refs_present": [],
                    "disclaimer_present": True,
                    "critical_failure": False,
                    "answer": "Answer with disclaimer. 本回答不構成法律意見。",
                    "latency_ms": ANY,
                },
                {
                    "id": "S2",
                    "persona": "Retail investor",
                    "scenario_type": "grounded",
                    "question": "forbidden",
                    "refused": False,
                    "expected_refusal": False,
                    "refusal_correct": True,
                    "citation_hit": True,
                    "required_refs_hit": True,
                    "any_of_refs_hit": False,
                    "forbidden_refs_present": [("privacy-finance", "第 5 條")],
                    "disclaimer_present": False,
                    "critical_failure": True,
                    "answer": "Answer without disclaimer.",
                    "latency_ms": ANY,
                },
            ],
        )


    def test_run_scenarios_marks_ref_misses_as_critical_failure(self) -> None:
        class FakeAgent:
            def answer(self, question: str) -> AgentResult:
                return AgentResult(
                    answer="Answer with disclaimer. 本回答不構成法律意見。",
                    refused=False,
                    citation_hit=True,
                    retrieved=[_retrieved_chunk("bank-act", "第 1 條")],
                )

        cases = [
            ScenarioCase(
                id="S3",
                persona="Compliance officer",
                scenario_type="grounded",
                question="missing-any-of",
                expect_refusal=False,
                required_refs=[],
                any_of_refs=[("insurance-act", "第 7 條")],
                forbidden_refs=[],
            ),
        ]

        report = run_scenarios(FakeAgent(), cases)

        self.assertEqual(report["critical_failures"], 1)
        self.assertTrue(report["results"][0]["critical_failure"])
        self.assertFalse(report["results"][0]["any_of_refs_hit"])

    def test_scenario_cli_runner_writes_full_report_and_prints_summary(self) -> None:
        module_path = ROOT / "eval" / "run_scenarios.py"
        spec = importlib.util.spec_from_file_location("run_scenarios_script", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cases = [
            ScenarioCase(
                id="S1",
                persona="Compliance officer",
                scenario_type="grounded",
                question="grounded",
                expect_refusal=False,
                required_refs=[("aml-finst", "第 2 條")],
                any_of_refs=[],
                forbidden_refs=[],
            )
        ]
        stdout = io.StringIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_root = module.ROOT
            module.ROOT = Path(temp_dir)
            (module.ROOT / "eval").mkdir(parents=True, exist_ok=True)

            class FakeSettings:
                api_key = "test-key"
                generation_model = "gen-model"
                embedding_model = "embed-model"
                retrieval_mode = "hybrid"
                vector_backend = "jsonl"
                min_retrieval_score = 0.01
                max_retrieval_rounds = 1

            class FakeRetriever:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

                def retrieve(self, question: str):
                    return [_retrieved_chunk("aml-finst", "第 2 條")]

                def retrieve_queries(self, queries: list[str]):
                    return [_retrieved_chunk("aml-finst", "第 2 條")]

            class FakeAgent:
                def __init__(self, **kwargs):
                    self.kwargs = kwargs

                def answer(self, question: str) -> AgentResult:
                    return AgentResult(
                        answer="Answer with disclaimer. 本回答不構成法律意見。",
                        refused=False,
                        citation_hit=True,
                        retrieved=[_retrieved_chunk("aml-finst", "第 2 條")],
                    )

            module.configure_utf8_stdio = lambda: None
            module.Settings = type("FakeSettingsFactory", (), {"from_env": staticmethod(lambda: FakeSettings())})
            module.GeminiClient = lambda *args: object()
            module.Retriever = FakeRetriever
            module.FinRagAgent = FakeAgent
            module.load_scenarios = lambda path: cases

            try:
                with contextlib.redirect_stdout(stdout):
                    exit_code = module.main()
            finally:
                module.ROOT = original_root

            self.assertEqual(exit_code, 0)
            report_path = Path(temp_dir) / "eval" / "last_scenarios_report.json"
            report = json.loads(report_path.read_text(encoding="utf-8"))

        printed_lines = stdout.getvalue().strip().splitlines()
        self.assertEqual(report["results"][0]["id"], "S1")
        summary = json.loads("\n".join(printed_lines[:-1]))
        self.assertNotIn("results", summary)
        self.assertEqual(summary["total"], report["total"])
        self.assertEqual(summary["critical_failures"], report["critical_failures"])
        self.assertEqual(printed_lines[-1], f"wrote {report_path}")


def _retrieved_chunk(doc_id: str, article: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            doc_id=doc_id,
            title=f"{doc_id} title",
            article=article,
            text="text",
            track="A",
            source_url="https://example.com",
            revision_date="2026-01-01",
        ),
        score=0.9,
    )


if __name__ == "__main__":
    unittest.main()
