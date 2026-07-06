from __future__ import annotations

from .bm25 import BM25Index
from .gemini import GeminiClient
from .types import Chunk, RetrievedChunk
from .vector_store import VectorRecord, hybrid_search, read_index, search


TITLE_DOC_HINTS: tuple[tuple[str, str], ...] = (
    ("證券交易法", "sit-securities-act"),
    ("個人資料保護法", "privacy-finance"),
    ("洗錢防制法", "aml-act"),
    ("金融機構防制洗錢辦法", "aml-finst"),
    ("證券投資信託基金管理辦法", "sit-fund-mgmt"),
    ("證券投資信託事業管理規則", "sit-biz-rules"),
    ("證券投資信託及顧問法", "sit-trust-act"),
    ("重大偶發事件", "sit-material-event"),
)


class Retriever:
    def __init__(
        self,
        *,
        client: GeminiClient,
        index_path: str,
        top_k: int = 12,
        retrieval_mode: str = "hybrid",
        rrf_k: int = 60,
    ):
        self.client = client
        self.index_path = index_path
        self.top_k = top_k
        self.retrieval_mode = retrieval_mode
        self.rrf_k = rrf_k
        self._records: list[VectorRecord] | None = None
        self._bm25_index: BM25Index | None = None

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        records = self._load_records()
        query_embedding = self.client.embed(question)
        if self.retrieval_mode == "embedding":
            ranked = search(records, query_embedding, len(records))
        else:
            ranked = hybrid_search(
                records,
                query_embedding,
                question,
                len(records),
                bm25_index=self._load_bm25_index(records),
                rrf_k=self.rrf_k,
            )
        return _apply_retrieval_hints(question, ranked, self.top_k)

    def _load_records(self) -> list[VectorRecord]:
        if self._records is None:
            self._records = read_index(self.index_path)
        return self._records

    def _load_bm25_index(self, records: list[VectorRecord]) -> BM25Index:
        if self._bm25_index is None:
            texts = [_chunk_search_text(record.chunk) for record in records]
            self._bm25_index = BM25Index.build(texts)
        return self._bm25_index


def _chunk_search_text(chunk: Chunk) -> str:
    return f"{chunk.title} {chunk.article} {chunk.text}"


def _retrieval_hints(question: str) -> list[tuple[str, str | None]]:
    hints: list[tuple[str, str | None]] = []
    for phrase, doc_id in TITLE_DOC_HINTS:
        if phrase in question:
            hints.append((doc_id, None))
    if "獨立董事" in question and "董事會" in question:
        hints.append(("sit-securities-act", "第 14-3 條"))
    elif "獨立董事" in question:
        hints.append(("sit-securities-act", "第 14-2 條"))
    if "利害關係" in question and "基金" in question:
        hints.append(("sit-fund-mgmt", "第 10 條"))
    if "董事" in question and "兼任" in question:
        hints.append(("sit-fund-mgmt", "第 11 條"))
        hints.append(("sit-biz-rules", "第 2 條"))
    return hints


def _apply_retrieval_hints(
    question: str,
    ranked: list[RetrievedChunk],
    top_k: int,
) -> list[RetrievedChunk]:
    hints = _retrieval_hints(question)
    if not hints:
        return ranked[:top_k]

    selected: list[RetrievedChunk] = []
    used: set[tuple[str, str]] = set()
    for doc_id, article in hints:
        match = _find_hint_match(ranked, doc_id, article)
        if match is None:
            continue
        key = (match.chunk.doc_id, match.chunk.article)
        if key in used:
            continue
        selected.append(match)
        used.add(key)

    for item in ranked:
        key = (item.chunk.doc_id, item.chunk.article)
        if key in used:
            continue
        selected.append(item)
        used.add(key)
        if len(selected) >= top_k:
            break
    return selected[:top_k]


def _find_hint_match(
    ranked: list[RetrievedChunk],
    doc_id: str,
    article: str | None,
) -> RetrievedChunk | None:
    if article is not None:
        return next(
            (
                item
                for item in ranked
                if item.chunk.doc_id == doc_id and item.chunk.article == article
            ),
            None,
        )
    return next((item for item in ranked if item.chunk.doc_id == doc_id), None)
