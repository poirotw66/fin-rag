from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .citations import citation_hit, looks_like_policy_refusal, should_refuse_question
from .gemini import GeminiClient
from .retrieval_assess import (
    is_retrieval_sufficient,
    merge_retrieved_chunks,
    retrieval_confidence,
)
from .types import RetrievedChunk


REFUSAL_POLICY = (
    "我不能判斷特定個案的裁罰金額、賠償責任或刑事責任。"
    "以下回答僅能依公開法規提供一般程序與條文方向，且不構成法律意見。"
)

REFUSAL_LOW_RETRIEVAL = (
    "依目前可檢索到的公開法規片段，不足以支持可靠回答。"
    "請改以更具體的法規名稱或條文關鍵詞重新提問。本回答不構成法律意見。"
)

REFUSAL_MESSAGES = {
    "policy": REFUSAL_POLICY,
    "low_retrieval": REFUSAL_LOW_RETRIEVAL,
    "citation": REFUSAL_POLICY,
}

MAX_GENERATION_ATTEMPTS = 3


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
        retrieve_queries: Callable[[list[str]], list[RetrievedChunk]] | None = None,
        system_prompt_path: str | Path | None = None,
        min_retrieval_score: float = 0.028,
        max_retrieval_rounds: int = 1,
    ):
        self.client = client
        self.retrieve = retrieve
        self.retrieve_queries = retrieve_queries or (lambda queries: retrieve(queries[0]))
        self.min_retrieval_score = min_retrieval_score
        self.max_retrieval_rounds = max_retrieval_rounds
        self.system_prompt = _read_system_prompt(system_prompt_path)
        self.retrieval_rewrite_prompt = _read_retrieval_rewrite_prompt()
        self.retrieval_rewrite_retry_prompt = _read_retrieval_rewrite_retry_prompt()
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
        graph.add_node("rewrite_query", self._rewrite_query_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("assess_retrieval", self._assess_retrieval_node)
        graph.add_node("rewrite_query_retry", self._rewrite_query_retry_node)
        graph.add_node("produce_answer", self._produce_answer_node)
        graph.add_node("refuse", self._refuse_node)
        graph.set_entry_point("classify")
        graph.add_conditional_edges(
            "classify",
            self._route_after_classify,
            {"refuse": "refuse", "rewrite_query": "rewrite_query"},
        )
        graph.add_edge("rewrite_query", "retrieve")
        graph.add_edge("retrieve", "assess_retrieval")
        graph.add_conditional_edges(
            "assess_retrieval",
            self._route_after_assess,
            {"produce_answer": "produce_answer", "rewrite_query_retry": "rewrite_query_retry", "refuse": "refuse"},
        )
        graph.add_edge("rewrite_query_retry", "retrieve")
        graph.add_conditional_edges(
            "produce_answer",
            self._route_after_produce,
            {"done": END, "refuse": "refuse"},
        )
        graph.add_edge("refuse", END)
        return graph.compile()

    def _route_after_classify(self, state: dict[str, Any]) -> str:
        return "refuse" if state["refuse_now"] else "rewrite_query"

    def _route_after_assess(self, state: dict[str, Any]) -> str:
        if state["retrieval_sufficient"]:
            return "produce_answer"
        if state.get("retrieval_round", 0) < self.max_retrieval_rounds:
            return "rewrite_query_retry"
        return "refuse"

    def _route_after_produce(self, state: dict[str, Any]) -> str:
        if state["citation_hit"]:
            return "done"
        state["refusal_reason"] = "citation"
        return "refuse"

    def _classify_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["refuse_now"] = should_refuse_question(state["question"])
        if state["refuse_now"]:
            state["refusal_reason"] = "policy"
        state.setdefault("retrieved", [])
        state.setdefault("retrieval_round", 0)
        state.setdefault("prior_queries", [])
        state.setdefault("citation_hit", False)
        state.setdefault("refused", False)
        state.setdefault("answer", "")
        return state

    def _rewrite_query_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["retrieval_round"] = 0
        state["prior_queries"] = []
        state["retrieval_queries"] = self._rewrite_for_retrieval(state["question"])
        state["prior_queries"] = list(state["retrieval_queries"])
        return state

    def _rewrite_query_retry_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["retrieval_round"] = state.get("retrieval_round", 0) + 1
        state["retrieval_queries"] = self._rewrite_for_retrieval_retry(state)
        state["prior_queries"] = list(
            dict.fromkeys([*state.get("prior_queries", []), *state["retrieval_queries"]])
        )
        return state

    def _rewrite_for_retrieval(self, question: str) -> list[str]:
        catalog = _read_corpus_catalog()
        prompt = (
            f"{self.retrieval_rewrite_prompt}\n\n"
            f"{catalog}\n\n"
            f"使用者問題:\n{question}\n\n"
            "請只輸出 1 至 3 行繁體中文檢索查詢，每行一句，不要其他說明。"
        )
        return self._parse_rewrite_lines(self.client.generate(prompt), question)

    def _rewrite_for_retrieval_retry(self, state: dict[str, Any]) -> list[str]:
        catalog = _read_corpus_catalog()
        weak_hits = _format_weak_retrieval_summary(state.get("retrieved", []))
        prior = "\n".join(f"- {query}" for query in state.get("prior_queries", [])) or "- （無）"
        prompt = (
            f"{self.retrieval_rewrite_retry_prompt}\n\n"
            f"{catalog}\n\n"
            f"使用者問題:\n{state['question']}\n\n"
            f"上一輪已試查詢:\n{prior}\n\n"
            f"上一輪檢索片段摘要:\n{weak_hits}\n\n"
            "請只輸出 1 至 3 行繁體中文檢索查詢，每行一句，不要其他說明。"
        )
        return self._parse_rewrite_lines(self.client.generate(prompt), state["question"])

    def _parse_rewrite_lines(self, rewritten: str, fallback: str) -> list[str]:
        lines = [line.strip() for line in rewritten.splitlines() if line.strip()]
        return lines or [fallback]

    def _retrieve_node(self, state: dict[str, Any]) -> dict[str, Any]:
        queries = list(dict.fromkeys([state["question"], *state.get("retrieval_queries", [])]))
        new_items = self.retrieve_queries(queries)
        if state.get("retrieval_round", 0) > 0 and state.get("retrieved"):
            state["retrieved"] = merge_retrieved_chunks(state["retrieved"], new_items)
        else:
            state["retrieved"] = new_items
        return state

    def _assess_retrieval_node(self, state: dict[str, Any]) -> dict[str, Any]:
        confidence = retrieval_confidence(state.get("retrieved", []))
        state["retrieval_confidence"] = confidence
        state["retrieval_sufficient"] = is_retrieval_sufficient(
            confidence,
            min_score=self.min_retrieval_score,
        )
        if (
            not state["retrieval_sufficient"]
            and state.get("retrieval_round", 0) >= self.max_retrieval_rounds
        ):
            state["refusal_reason"] = "low_retrieval"
        return state

    def _generate_node(self, state: dict[str, Any]) -> dict[str, Any]:
        context = "\n\n".join(
            f"[{item.chunk.doc_id} {item.chunk.article}] {item.chunk.title}: {item.chunk.text}"
            for item in state["retrieved"]
        )
        hints = _format_citation_hints(state["retrieved"])
        retry_note = state.get("generation_retry_note", "")
        prompt = (
            f"{self.system_prompt}\n\n{hints}\n\n公開法規片段:\n{context}\n\n"
            f"使用者問題:\n{state['question']}{retry_note}\n\n請用繁體中文回答。"
        )
        state["answer"] = self.client.generate(prompt)
        return state

    def _build_generation_retry_note(self, state: dict[str, Any]) -> str:
        if looks_like_policy_refusal(state.get("answer", "")):
            return (
                "\n\n上一輪誤判為拒答。此為一般法規問題（比較、程序、定義或個資蒐集要件），"
                "請依檢索片段回答，且每個事實句附上（doc_id 第 N 條）。"
            )
        return (
            "\n\n上一輪回答未通過引用檢查。"
            "請務必在每個法規事實句附上（doc_id 第 N 條），且 doc_id 與條號必須來自上方可用引用清單或片段。"
        )

    def _citation_check_node(self, state: dict[str, Any]) -> dict[str, Any]:
        state["citation_hit"] = citation_hit(state["answer"], state["retrieved"])
        return state

    def _produce_answer_node(self, state: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            state["generation_retry_note"] = self._build_generation_retry_note(state) if attempt else ""
            state = self._generate_node(state)
            if (
                not state.get("refuse_now")
                and looks_like_policy_refusal(state["answer"])
                and attempt < MAX_GENERATION_ATTEMPTS - 1
            ):
                continue
            state = self._citation_check_node(state)
            if state["citation_hit"]:
                break
        return state

    def _refuse_node(self, state: dict[str, Any]) -> dict[str, Any]:
        reason = state.get("refusal_reason", "policy")
        state["answer"] = REFUSAL_MESSAGES.get(reason, REFUSAL_POLICY)
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
        state = self.agent._rewrite_query_node(state)
        while True:
            state = self.agent._retrieve_node(state)
            state = self.agent._assess_retrieval_node(state)
            if state["retrieval_sufficient"]:
                break
            if state.get("retrieval_round", 0) < self.agent.max_retrieval_rounds:
                state = self.agent._rewrite_query_retry_node(state)
                continue
            state["refusal_reason"] = "low_retrieval"
            return self.agent._refuse_node(state)
        state = self.agent._produce_answer_node(state)
        if not state["citation_hit"]:
            state["refusal_reason"] = "citation"
            state = self.agent._refuse_node(state)
        return state


def _read_system_prompt(path: str | Path | None) -> str:
    prompt_path = Path(path) if path else Path(__file__).resolve().parent / "prompts" / "system.md"
    return prompt_path.read_text(encoding="utf-8")


def _read_retrieval_rewrite_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "retrieval_rewrite.md"
    return prompt_path.read_text(encoding="utf-8")


def _read_retrieval_rewrite_retry_prompt() -> str:
    prompt_path = Path(__file__).resolve().parent / "prompts" / "retrieval_rewrite_retry.md"
    return prompt_path.read_text(encoding="utf-8")


def _read_corpus_catalog() -> str:
    manifest_path = Path(__file__).resolve().parents[2] / "corpus" / "manifest.json"
    if not manifest_path.exists():
        return ""
    entries = json.loads(manifest_path.read_text(encoding="utf-8"))
    lines = [f"- {entry['doc_id']}: {entry['title']}" for entry in entries]
    return "本系統 corpus 收錄法規（doc_id: 標題）:\n" + "\n".join(lines)


def _format_weak_retrieval_summary(retrieved: list[RetrievedChunk], limit: int = 5) -> str:
    if not retrieved:
        return "- （無）"
    lines: list[str] = []
    for item in retrieved[:limit]:
        lines.append(f"- {item.chunk.doc_id} {item.chunk.article} {item.chunk.title} (score={item.score:.4f})")
    return "\n".join(lines)


def _format_citation_hints(retrieved: list[RetrievedChunk], limit: int = 10) -> str:
    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for item in retrieved:
        key = (item.chunk.doc_id, item.chunk.article)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {item.chunk.doc_id} {item.chunk.article}")
        if len(lines) >= limit:
            break
    if not lines:
        return "可用引用（doc_id 第 N 條）:\n- （無）"
    return "可用引用（doc_id 第 N 條）:\n" + "\n".join(lines)
