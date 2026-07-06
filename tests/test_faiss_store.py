import tempfile
import unittest
from pathlib import Path

from fin_rag.bm25 import BM25Index, read_bm25_index
from fin_rag.types import Chunk
from fin_rag.vector_store import (
    VectorRecord,
    chunk_search_text,
    hybrid_search,
    hybrid_search_loaded_index,
    load_index_bundle,
    search,
    write_bm25_bundle,
    write_faiss_bundle,
)


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


class FaissStoreTests(unittest.TestCase):
    def test_faiss_search_matches_jsonl_search(self) -> None:
        records = [
            VectorRecord(_chunk("aml-finst", "第 2 條", "風險基礎方法"), [1.0, 0.0, 0.0]),
            VectorRecord(_chunk("aml-finst", "第 7 條", "客戶身分確認"), [0.0, 1.0, 0.0]),
            VectorRecord(_chunk("aml-finst", "第 12 條", "交易紀錄保存"), [0.0, 0.0, 1.0]),
        ]
        query = [0.0, 1.0, 0.0]

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jsonl_path = root / "index.jsonl"
            write_faiss_bundle(records, jsonl_path)
            bundle = load_index_bundle(jsonl_path, backend="faiss")

            jsonl_hits = search(records, query, top_k=2)
            faiss_hits = bundle.faiss_index.search(query, top_k=2) if bundle.faiss_index else []

        self.assertEqual(
            [(item.chunk.doc_id, item.chunk.article) for item in jsonl_hits],
            [(item.chunk.doc_id, item.chunk.article) for item in faiss_hits],
        )

    def test_hybrid_search_loaded_index_matches_records_path(self) -> None:
        records = [
            VectorRecord(_chunk("aml-finst", "第 2 條", "風險基礎方法定義"), [1.0, 0.0, 0.0]),
            VectorRecord(_chunk("aml-finst", "第 7 條", "客戶身分確認程序"), [0.0, 1.0, 0.0]),
            VectorRecord(_chunk("aml-finst", "第 12 條", "交易紀錄保存期限"), [0.0, 0.0, 1.0]),
        ]
        bm25 = BM25Index.build([f"{record.chunk.title} {record.chunk.article} {record.chunk.text}" for record in records])
        query_embedding = [0.0, 0.0, 1.0]
        query_text = "客戶身分確認"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            jsonl_path = root / "index.jsonl"
            write_faiss_bundle(records, jsonl_path)
            bundle = load_index_bundle(jsonl_path, backend="faiss")

            record_hits = hybrid_search(records, query_embedding, query_text, 2, bm25_index=bm25)
            faiss_hits = hybrid_search_loaded_index(
                bundle,
                query_embedding,
                query_text,
                2,
                bm25_index=bm25,
            )

        self.assertEqual(
            [(item.chunk.article, item.chunk.doc_id) for item in record_hits],
            [(item.chunk.article, item.chunk.doc_id) for item in faiss_hits],
        )

    def test_bm25_persist_round_trip_matches_in_memory_build(self) -> None:
        records = [
            VectorRecord(_chunk("aml-finst", "第 7 條", "客戶身分確認程序"), [0.0, 1.0, 0.0]),
            VectorRecord(_chunk("aml-finst", "第 12 條", "交易紀錄保存期限"), [0.0, 0.0, 1.0]),
        ]
        texts = [chunk_search_text(record.chunk) for record in records]
        built = BM25Index.build(texts)

        with tempfile.TemporaryDirectory() as temp_dir:
            jsonl_path = Path(temp_dir) / "index.jsonl"
            write_bm25_bundle(records, jsonl_path)
            loaded = read_bm25_index(jsonl_path.parent / "index_bm25.json")

        self.assertEqual(built.score("客戶身分確認"), loaded.score("客戶身分確認"))


if __name__ == "__main__":
    unittest.main()
