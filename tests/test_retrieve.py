import unittest

from fin_rag.bm25 import BM25Index, tokenize
from fin_rag.retrieve import _apply_retrieval_hints
from fin_rag.types import Chunk, RetrievedChunk
from fin_rag.vector_store import VectorRecord, hybrid_search, search


def _chunk(doc_id: str, article: str, text: str) -> Chunk:
    return Chunk(
        doc_id=doc_id,
        title=doc_id,
        article=article,
        text=text,
        track="test",
        source_url="https://example.test",
        revision_date="113-01-01",
    )


def _record(doc_id: str, article: str, text: str, embedding: list[float]) -> VectorRecord:
    return VectorRecord(chunk=_chunk(doc_id, article, text), embedding=embedding)


class BM25Tests(unittest.TestCase):
    def test_tokenize_keeps_cjk_characters_and_alphanumeric_words(self) -> None:
        self.assertEqual(tokenize("CDD 客戶身分確認"), ["cdd", "客", "戶", "身", "分", "確", "認"])

    def test_bm25_prefers_lexical_match(self) -> None:
        index = BM25Index.build(
            [
                "風險基礎方法定義",
                "客戶身分確認程序",
                "交易紀錄保存期限",
            ]
        )

        scores = index.score("客戶身分確認")

        self.assertGreater(scores[1], scores[0])
        self.assertGreater(scores[1], scores[2])


class HybridSearchTests(unittest.TestCase):
    def test_hybrid_search_combines_embedding_and_bm25_rankings(self) -> None:
        records = [
            _record("aml-finst", "第 2 條", "風險基礎方法定義", [1.0, 0.0, 0.0]),
            _record("aml-finst", "第 7 條", "客戶身分確認程序", [0.0, 1.0, 0.0]),
            _record("aml-finst", "第 12 條", "交易紀錄保存期限", [0.0, 0.0, 1.0]),
        ]
        bm25_index = BM25Index.build([f"{record.chunk.title} {record.chunk.article} {record.chunk.text}" for record in records])

        lexical_results = hybrid_search(
            records,
            [0.0, 0.0, 1.0],
            "客戶身分確認",
            top_k=2,
            bm25_index=bm25_index,
            rrf_k=60,
        )
        embedding_only = search(records, [0.0, 0.0, 1.0], top_k=2)

        self.assertEqual(lexical_results[0].chunk.article, "第 7 條")
        self.assertEqual(embedding_only[0].chunk.article, "第 12 條")


class RetrievalHintTests(unittest.TestCase):
    def test_apply_retrieval_hints_injects_expected_law_article(self) -> None:
        ranked = [
            _record("sit-trust-act", "第 59 條", "全權委託限制", [0.0, 0.0, 1.0]),
            _record("sit-fund-mgmt", "第 54 條", "私募基金限制", [0.0, 1.0, 0.0]),
            _record("sit-fund-mgmt", "第 10 條", "基金不得投資利害關係公司證券", [1.0, 0.0, 0.0]),
        ]
        ranked = [
            RetrievedChunk(chunk=record.chunk, score=index / 10)
            for index, record in enumerate(ranked)
        ]

        results = _apply_retrieval_hints(
            "全委帳戶與基金對利害關係人交易限制有何不同？",
            ranked,
            top_k=2,
        )

        self.assertEqual(results[0].chunk.doc_id, "sit-fund-mgmt")
        self.assertEqual(results[0].chunk.article, "第 10 條")


if __name__ == "__main__":
    unittest.main()
