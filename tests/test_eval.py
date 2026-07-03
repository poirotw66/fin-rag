import tempfile
import unittest
from pathlib import Path

from fin_rag.eval import load_golden


class EvalTests(unittest.TestCase):
    def test_load_golden_reads_json_yaml_subset(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "golden.yaml"
            path.write_text(
                '[{"id":"C1","track":"C","question":"罰多少？","expected_refs":[],"expect_refusal":true}]',
                encoding="utf-8",
            )

            cases = load_golden(path)

        self.assertEqual(cases[0].id, "C1")
        self.assertTrue(cases[0].expect_refusal)


if __name__ == "__main__":
    unittest.main()

