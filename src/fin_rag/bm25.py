from __future__ import annotations

import math
import re
from dataclasses import dataclass


_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+")


def tokenize(text: str) -> list[str]:
    return [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]


@dataclass
class BM25Index:
    corpus: list[list[str]]
    k1: float = 1.5
    b: float = 0.75
    doc_lens: list[int] | None = None
    avgdl: float = 0.0
    idf: dict[str, float] | None = None

    @classmethod
    def build(cls, texts: list[str], *, k1: float = 1.5, b: float = 0.75) -> "BM25Index":
        corpus = [tokenize(text) for text in texts]
        index = cls(corpus=corpus, k1=k1, b=b)
        index._prepare()
        return index

    def _prepare(self) -> None:
        self.doc_lens = [len(doc) for doc in self.corpus]
        doc_count = len(self.corpus)
        self.avgdl = sum(self.doc_lens) / doc_count if doc_count else 0.0
        document_frequency: dict[str, int] = {}
        for doc in self.corpus:
            for term in set(doc):
                document_frequency[term] = document_frequency.get(term, 0) + 1
        self.idf = {
            term: math.log((doc_count - frequency + 0.5) / (frequency + 0.5) + 1.0)
            for term, frequency in document_frequency.items()
        }

    def score(self, query: str) -> list[float]:
        if not self.corpus or self.idf is None or self.doc_lens is None:
            return []
        query_tokens = tokenize(query)
        scores = [0.0] * len(self.corpus)
        for term in query_tokens:
            inverse_document_frequency = self.idf.get(term)
            if inverse_document_frequency is None:
                continue
            for doc_index, doc in enumerate(self.corpus):
                term_frequency = doc.count(term)
                if term_frequency == 0:
                    continue
                doc_length = self.doc_lens[doc_index]
                denominator = term_frequency + self.k1 * (
                    1.0 - self.b + self.b * doc_length / self.avgdl
                )
                scores[doc_index] += inverse_document_frequency * (
                    term_frequency * (self.k1 + 1.0)
                ) / denominator
        return scores
