from __future__ import annotations

from .bm25 import BM25Index, read_bm25_index
from .gemini import GeminiClient
from .types import Chunk, RetrievedChunk
from .vector_store import (
    LoadedIndex,
    bm25_path_for,
    chunk_search_text,
    hybrid_search_loaded_index,
    load_index_bundle,
    rank_loaded_index,
)


class Retriever:
    def __init__(
        self,
        *,
        client: GeminiClient,
        index_path: str,
        top_k: int = 12,
        retrieval_mode: str = "hybrid",
        vector_backend: str = "auto",
        rrf_k: int = 60,
    ):
        self.client = client
        self.index_path = index_path
        self.top_k = top_k
        self.retrieval_mode = retrieval_mode
        self.vector_backend = vector_backend
        self.rrf_k = rrf_k
        self._bundle: LoadedIndex | None = None
        self._bm25_index: BM25Index | None = None

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        bundle = self._load_bundle()
        query_embedding = self.client.embed(question)
        if self.retrieval_mode == "embedding":
            ranked = rank_loaded_index(bundle, query_embedding)
        else:
            ranked = hybrid_search_loaded_index(
                bundle,
                query_embedding,
                question,
                len(bundle.chunks),
                bm25_index=self._load_bm25_index(bundle.chunks),
                rrf_k=self.rrf_k,
            )
        return _apply_retrieval_hints(question, ranked, self.top_k)

    def _load_bundle(self) -> LoadedIndex:
        if self._bundle is None:
            self._bundle = load_index_bundle(self.index_path, backend=self.vector_backend)
        return self._bundle

    def _load_bm25_index(self, chunks: list[Chunk]) -> BM25Index:
        if self._bm25_index is None:
            bm25_path = bm25_path_for(self.index_path)
            if bm25_path.exists():
                self._bm25_index = read_bm25_index(bm25_path)
                if len(self._bm25_index.corpus) != len(chunks):
                    raise ValueError("BM25 index size does not match loaded chunks")
            else:
                self._bm25_index = BM25Index.build([chunk_search_text(chunk) for chunk in chunks])
        return self._bm25_index


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
