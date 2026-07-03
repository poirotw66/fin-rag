from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .citations import citation_hit, should_refuse_question
from .gemini import GeminiClient
from .types import RetrievedChunk


REFUSAL = (
    "我不能判斷特定個案的裁罰金額、賠償責任或刑事責任。"
    "以下回答僅能依公開法規提供一般程序與條文方向，且不構成法律意見。"
)


@dataclass(frozen=True)
class AgentResult:
    answer: str
    refused: bool
    citation_hit: bool
    retrieved: list[RetrievedChunk]


class FinRagAgent:
    def __init__(
        self,
        *,
        client: GeminiClient,
        retrieve: Callable[[str], list[RetrievedChunk]],
        system_prompt_path: str | Path | None = None,
    ):
        self.client = client
        self.retrieve = retrieve
        self.system_prompt = _read_system_prompt(system_prompt_path)
        self.graph = self._build_graph()

    def answer(self, question: str) -> AgentResult:
        state = self.graph.invoke({"question": question})
        return AgentResult(
            answer=state["answer"],
            refused=state["refused"],
            citation_hit=state["citation_hit"],
            retrieved=state["retrieved"],
        )

    def _build_graph(self):
        try:
            from langgraph.graph import END, StateGraph
        except Exception:
            return _SequentialGraph(self)

        graph = StateGraph(dict)
        graph.add_node("classify", self._classify_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("generate", self._generate_node)
        graph.add_node("citation_check", self._citation_check_node)
        graph.add_node("refuse", self._refuse_node)
        graph.set_entry_point("classify")
        graph.add_conditional_edges(
            "classify",
            lambda state: "refuse" if state["refuse_now"] else "retrieve",
            {"refuse": "refuse", "retrieve": "retrieve"},
        )
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", "citation_check")
        graph.add_conditional_edges(
            "citation_check",
            lambda state: "done" if state["citation_hit"] else "refuse",
            {"done": END, "refuse": "refuse"},
        )
        graph.add_edge("refuse", END)
        return graph.compile()

    def _classify_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["refuse_now"] = should_refuse_question(state["question"])
        state.setdefault("retrieved", [])
        state.setdefault("citation_hit", False)
        state.setdefault("refused", False)
        state.setdefault("answer", "")
        return state

    def _retrieve_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["retrieved"] = self.retrieve(state["question"])
        return state

    def _generate_node(self, state: dict[str, Any]) -> dict[str, Any]:
        context = "\n\n".join(
            f"[{item.chunk.doc_id} {item.chunk.article}] {item.chunk.title}: {item.chunk.text}"
            for item in state["retrieved"]
        )
        prompt = f"{self.system_prompt}\n\n公開法規片段:\n{context}\n\n使用者問題:\n{state['question']}\n\n請用繁體中文回答。"
        state["answer"] = self.client.generate(prompt)
        return state

    def _citation_check_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["citation_hit"] = citation_hit(state["answer"], state["retrieved"])
        return state

    def _refuse_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["answer"] = REFUSAL
        state["refused"] = True
        state["citation_hit"] = False
        return state


class _SequentialGraph:
    def __init__(self, agent: FinRagAgent):
        self.agent = agent

    def invoke(self, state: dict[str, Any]) -> dict[str, Any]:
        state = self.agent._classify_node(state)
        if state["refuse_now"]:
            return self.agent._refuse_node(state)
        state = self.agent._retrieve_node(state)
        state = self.agent._generate_node(state)
        state = self.agent._citation_check_node(state)
        if not state["citation_hit"]:
            state = self.agent._refuse_node(state)
        return state


def _read_system_prompt(path: str | Path | None) -> str:
    prompt_path = Path(path) if path else Path(__file__).resolve().parent / "prompts" / "system.md"
    return prompt_path.read_text(encoding="utf-8")

