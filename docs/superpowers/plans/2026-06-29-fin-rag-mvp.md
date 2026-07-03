# Fin RAG MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete CLI-first financial regulation Agentic RAG MVP with Gemini generation, Gemini embeddings, LangGraph flow, corpus chunking, retrieval, and golden-set eval.

**Architecture:** Python package `fin_rag` owns corpus loading, chunking, vector retrieval, Gemini clients, citation checking, and LangGraph agent orchestration. CLI scripts generate chunks, build the vector index, ask questions, and run eval.

**Tech Stack:** Python 3.11+, `google-genai`, `langgraph`, `numpy`, `pyyaml`, `pytest`, `requests`, `beautifulsoup4`.

---

### Task 1: Project Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `README.md`
- Create: `src/fin_rag/__init__.py`
- Create: `src/fin_rag/config.py`
- Create: `tests/test_config.py`

- [x] Write tests for default Gemini model names and env loading.
- [x] Run tests and verify they fail before implementation.
- [x] Implement config.
- [x] Run tests and verify they pass.

### Task 2: Corpus Manifest And Chunking

**Files:**
- Create: `corpus/manifest.json`
- Create: `corpus/README.md`
- Create: `corpus/raw/*.txt`
- Create: `src/fin_rag/types.py`
- Create: `src/fin_rag/corpus.py`
- Create: `scripts/chunk_by_article.py`
- Create: `tests/test_corpus.py`

- [x] Write tests for manifest loading and article parsing.
- [x] Run tests and verify they fail before implementation.
- [x] Implement corpus loading and article chunking.
- [x] Run tests and verify they pass.

### Task 3: Retrieval And Vector Store

**Files:**
- Create: `src/fin_rag/embeddings.py`
- Create: `src/fin_rag/vector_store.py`
- Create: `src/fin_rag/retrieve.py`
- Create: `scripts/build_index.py`
- Create: `tests/test_retrieve.py`

- [x] Write deterministic fake embedding tests for top-k retrieval.
- [x] Run tests and verify they fail before implementation.
- [x] Implement embedding ports, JSON index, cosine retrieval.
- [x] Run tests and verify they pass.

### Task 4: Citations And Classification

**Files:**
- Create: `src/fin_rag/citations.py`
- Create: `tests/test_citations.py`

- [x] Write tests for cited article hit/miss and refusal classification.
- [x] Run tests and verify they fail before implementation.
- [x] Implement citation extraction, citation hit, and sensitive-question classification.
- [x] Run tests and verify they pass.

### Task 5: Gemini LLM And LangGraph Agent

**Files:**
- Create: `src/fin_rag/llm.py`
- Create: `src/fin_rag/agent.py`
- Create: `src/fin_rag/prompts/system.md`
- Create: `scripts/ask.py`
- Create: `tests/test_agent.py`

- [x] Write tests for refusal routing and cited answer routing with fake LLM/retriever.
- [x] Run tests and verify they fail before implementation.
- [x] Implement Gemini LLM wrapper and LangGraph graph.
- [x] Run tests and verify they pass.

### Task 6: Golden Eval

**Files:**
- Create: `eval/golden.yaml`
- Create: `src/fin_rag/eval.py`
- Create: `eval/run.py`
- Create: `tests/test_eval.py`

- [x] Write tests for metrics and JSON report shape.
- [x] Run tests and verify they fail before implementation.
- [x] Implement eval runner.
- [x] Run tests and verify they pass.

### Task 7: Verification

**Files:**
- Modify: `README.md`

- [x] Run full test suite.
- [x] Document setup, Gemini API key, chunk/index/eval commands, and legal disclaimer.

