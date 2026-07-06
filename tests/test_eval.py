import tempfile
import unittest
from pathlib import Path

from fin_rag.agent import AgentResult
from fin_rag.eval import GoldenCase, load_golden, run_eval


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


if __name__ == "__main__":
    unittest.main()
