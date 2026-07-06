import unittest

from fin_rag.retrieval_assess import (
    is_retrieval_sufficient,
    merge_retrieved_chunks,
    retrieval_confidence,
)
from fin_rag.types import Chunk, RetrievedChunk


def _chunk(doc_id: str, article: str) -> Chunk:
    return Chunk(
        doc_id=doc_id,
        title=doc_id,
        article=article,
        text="text",
        track="test",
        source_url="https://example.test",
        revision_date="113-01-01",
    )


class RetrievalAssessTests(unittest.TestCase):
    def test_retrieval_confidence_uses_max_score(self) -> None:
        retrieved = [
            RetrievedChunk(_chunk("aml-finst", "第 2 條"), 0.05),
            RetrievedChunk(_chunk("aml-finst", "第 7 條"), 0.03),
        ]

        self.assertAlmostEqual(retrieval_confidence(retrieved), 0.05)

    def test_retrieval_confidence_is_zero_when_empty(self) -> None:
        self.assertEqual(retrieval_confidence([]), 0.0)

    def test_is_retrieval_sufficient_compares_against_threshold(self) -> None:
        self.assertTrue(is_retrieval_sufficient(0.03, min_score=0.028))
        self.assertFalse(is_retrieval_sufficient(0.02, min_score=0.028))

    def test_merge_retrieved_chunks_keeps_best_score_per_chunk(self) -> None:
        existing = [RetrievedChunk(_chunk("sit-fund-mgmt", "第 10 條"), 0.02)]
        new_items = [
            RetrievedChunk(_chunk("sit-fund-mgmt", "第 10 條"), 0.04),
            RetrievedChunk(_chunk("sit-biz-rules", "第 2 條"), 0.03),
        ]

        merged = merge_retrieved_chunks(existing, new_items)

        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0].chunk.article, "第 10 條")
        self.assertAlmostEqual(merged[0].score, 0.04)


if __name__ == "__main__":
    unittest.main()
