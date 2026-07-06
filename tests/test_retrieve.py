import unittest

from fin_rag.bm25 import BM25Index, tokenize
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


class MultiQueryRetrieveTests(unittest.TestCase):
    def test_retrieve_queries_merges_best_score_per_chunk(self) -> None:
        from fin_rag.retrieve import Retriever

        records = [
            _record("aml-finst", "第 7 條", "客戶身分確認程序", [0.0, 1.0, 0.0]),
            _record("aml-finst", "第 12 條", "交易紀錄保存期限", [0.0, 0.0, 1.0]),
        ]

        class FakeClient:
            def embed(self, text: str) -> list[float]:
                if "客戶" in text:
                    return [0.0, 1.0, 0.0]
                return [0.0, 0.0, 1.0]

        retriever = Retriever.__new__(Retriever)
        retriever.client = FakeClient()
        retriever.index_path = "unused"
        retriever.top_k = 2
        retriever.retrieval_mode = "embedding"
        retriever.vector_backend = "jsonl"
        retriever.rrf_k = 60
        retriever._bundle = None
        retriever._bm25_index = None
        def fake_retrieve(query: str) -> list[RetrievedChunk]:
            if "客戶" in query:
                return [
                    RetrievedChunk(chunk=records[0].chunk, score=0.9),
                    RetrievedChunk(chunk=records[1].chunk, score=0.1),
                ]
            return [
                RetrievedChunk(chunk=records[1].chunk, score=0.9),
                RetrievedChunk(chunk=records[0].chunk, score=0.1),
            ]

        retriever.retrieve = fake_retrieve

        results = retriever.retrieve_queries(["客戶身分確認", "交易紀錄保存"])

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].chunk.article, "第 7 條")
        self.assertEqual(results[1].chunk.article, "第 12 條")


if __name__ == "__main__":
    unittest.main()
