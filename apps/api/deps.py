from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from fastapi import HTTPException

from .runtime import build_agent

if TYPE_CHECKING:
    from fin_rag.agent import FinRagAgent


class AgentLike(Protocol):
    def answer(self, question: str) -> object:
        ...


def get_agent() -> "FinRagAgent":
    try:
        return build_agent()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
