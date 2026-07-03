from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from fin_rag.agent import FinRagAgent


class AgentLike(Protocol):
    def answer(self, question: str) -> object:
        ...


def get_agent() -> "FinRagAgent":
    raise NotImplementedError("Wire real agent in Task 3")
