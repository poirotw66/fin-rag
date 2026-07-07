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

KNOWN_DOC_IDS = (
    "aml-act",
    "aml-bank-ic",
    "aml-finst",
    "bank-act",
    "fhc-act",
    "futures-act",
    "insurance-act",
    "insurance-aml-ic",
    "privacy-finance",
    "sit-advisor-mgmt",
    "sit-biz-rules",
    "sit-fund-mgmt",
    "sit-material-event",
    "sit-securities-act",
    "sit-trust-act",
    "trust-industry-act",
)

ARTICLE_BODY = (
    r"第\s*"
    r"[\d一二三四五六七八九十百千]+"
    r"(?:-[\d一二三四五六七八九十百千]+)?"
    r"(?:之\s*[\d一二三四五六七八九十百千]+)?"
    r"\s*條"
)
ARTICLE_CITATION_RE = re.compile(
    rf"([\w\-\u4e00-\u9fff、及與（）()]+?)\s*({ARTICLE_BODY})"
)
PARAGRAPH_CITATION_RE = re.compile(r"([\w\-\u4e00-\u9fff、及與]+?)\s*(paragraph-\d+)")
INLINE_DOC_CITATION_RE = re.compile(
    rf"\b((?:{'|'.join(KNOWN_DOC_IDS)}))\s*({ARTICLE_BODY})"
)
PAREN_RE = re.compile(r"[（(]([^（）()]+)[）)]")


def should_refuse_question(question: str) -> bool:
    return any(pattern in question for pattern in CASE_SPECIFIC_PATTERNS)


POLICY_REFUSAL_MARKERS = (
    "我不能判斷特定個案的裁罰金額",
    "賠償責任或刑事責任",
)


def looks_like_policy_refusal(answer: str) -> bool:
    return any(marker in answer for marker in POLICY_REFUSAL_MARKERS)


def extract_citations(answer: str) -> set[tuple[str, str]]:
    citations: set[tuple[str, str]] = set()
    for text in [match.group(1) for match in PAREN_RE.finditer(answer)]:
        citations.update(_extract_from_text(text))
    citations.update(_extract_inline_doc_citations(answer))
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


def _extract_from_text(text: str) -> set[tuple[str, str]]:
    citations: set[tuple[str, str]] = set()
    for match in ARTICLE_CITATION_RE.finditer(text):
        citations.add((_normalize(match.group(1)), _canonical_article(match.group(2))))
    for match in PARAGRAPH_CITATION_RE.finditer(text):
        citations.add((_normalize(match.group(1)), _normalize(match.group(2))))
    return citations


def _extract_inline_doc_citations(answer: str) -> set[tuple[str, str]]:
    return {
        (_normalize(match.group(1)), _canonical_article(match.group(2)))
        for match in INLINE_DOC_CITATION_RE.finditer(answer)
    }


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
