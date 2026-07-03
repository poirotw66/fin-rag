from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ManifestEntry:
    doc_id: str
    title: str
    source_url: str
    issuer: str
    revision_date: str
    fetched_at: str
    format: str
    chunk_strategy: str
    track: str


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    title: str
    article: str
    text: str
    track: str
    source_url: str
    revision_date: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Chunk":
        return cls(**data)


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float

