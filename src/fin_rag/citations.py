from __future__ import annotations

import re

from .types import RetrievedChunk


CASE_SPECIFIC_PATTERNS = [
    "會被罰多少",
    "罰多少",
    "誰賠",
    "賠償多少",
    "4.54 億",
    "4.54億",
    "300 萬",
    "300萬",
    "刑事責任",
]

PAREN_RE = re.compile(r"[（(]([^（）()]+)[）)]")
ARTICLE_CITATION_RE = re.compile(r"([\w\-\u4e00-\u9fff、及與]+?)\s*(第\s*[一二三四五六七八九十百千\d]+\s*條(?:之\s*[一二三四五六七八九十百千\d]+)?)")
PARAGRAPH_CITATION_RE = re.compile(r"([\w\-\u4e00-\u9fff、及與]+?)\s*(paragraph-\d+)")


def should_refuse_question(question: str) -> bool:
    return any(pattern in question for pattern in CASE_SPECIFIC_PATTERNS)


def extract_citations(answer: str) -> set[tuple[str, str]]:
    citation_texts = [match.group(1) for match in PAREN_RE.finditer(answer)]
    citations = set()
    for text in citation_texts:
        citations.update((_normalize(match.group(1)), _canonical_article(match.group(2))) for match in ARTICLE_CITATION_RE.finditer(text))
        citations.update((_normalize(match.group(1)), _normalize(match.group(2))) for match in PARAGRAPH_CITATION_RE.finditer(text))
    return citations


def citation_hit(answer: str, retrieved: list[RetrievedChunk]) -> bool:
    citations = extract_citations(answer)
    available = set()
    for item in retrieved:
        article = _canonical_article(item.chunk.article)
        available.add((_normalize(item.chunk.doc_id), article))
        available.add((_normalize(item.chunk.title), article))
    if citations and citations.issubset(available):
        return True
    return _title_only_paragraph_hit(answer, retrieved)


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _canonical_article(value: str) -> str:
    return re.sub(r"\s+", "", value).strip()


def _title_only_paragraph_hit(answer: str, retrieved: list[RetrievedChunk]) -> bool:
    for item in retrieved:
        if not item.chunk.article.startswith("paragraph-"):
            continue
        if item.chunk.doc_id in answer or item.chunk.title in answer:
            return True
    return False
