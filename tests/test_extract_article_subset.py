import unittest

from fin_rag.corpus import extract_articles


class ExtractArticleSubsetTests(unittest.TestCase):
    def test_extract_articles_keeps_requested_blocks(self) -> None:
        source = (
            "第 1 條\n"
            "first body\n\n"
            "第 2 條\n"
            "second body\n\n"
            "第 3 條\n"
            "third body\n"
        )

        result = extract_articles(source, ["第 2 條"])

        self.assertIn("第 2 條", result)
        self.assertIn("second body", result)
        self.assertNotIn("first body", result)
        self.assertNotIn("third body", result)


if __name__ == "__main__":
    unittest.main()
