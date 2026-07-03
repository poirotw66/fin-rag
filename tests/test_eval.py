import tempfile
import unittest
from pathlib import Path

from fin_rag.eval import load_golden


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


if __name__ == "__main__":
    unittest.main()
