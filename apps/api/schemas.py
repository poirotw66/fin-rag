from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


class CitationResponse(BaseModel):
    doc_id: str
    article: str
    title: str


class RetrievedChunkResponse(BaseModel):
    doc_id: str
    title: str
    article: str
    text: str
    score: float


class AskResponse(BaseModel):
    question: str
    answer: str
    refused: bool
    citation_hit: bool
    citations: list[CitationResponse]
    retrieved: list[RetrievedChunkResponse]
