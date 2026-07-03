# Fin RAG MVP Design

## Goal

Build a CLI-first financial regulation Agentic RAG MVP that uses public legal corpus, Gemini for generation, Gemini embeddings for retrieval, LangGraph for answer flow, and a reproducible golden-set evaluation.

## Scope

The MVP includes:

- Track B: investment trust related-party and material-event compliance questions.
- Track A: AML and internal-control compliance questions.
- Track C: refusal behavior for case-specific penalties, compensation, and unstable news claims.
- Corpus manifest, raw source folder, article chunks, retrieval index, LangGraph agent, CLI, and eval runner.

The MVP excludes a web UI, private/internal regulations, enforcement-news corpus, and legal advice.

## Architecture

The system is a small Python package with scripts for ingestion/chunking and CLIs for asking questions and running eval.

LangGraph models the agent flow:

1. `classify_question`: route obvious penalty, compensation, and out-of-scope questions to refusal.
2. `retrieve`: embed the question and fetch top-k chunks.
3. `generate`: call Gemini with retrieved chunks and the system prompt.
4. `citation_check`: verify that cited document/article pairs exist in retrieved chunks.
5. `finalize` or `refuse`: return either a cited answer or a controlled refusal.

Gemini is accessed behind small ports:

- `GeminiLLM` for generation, default `gemini-2.5-flash`.
- `GeminiEmbeddingClient` for embeddings, default `gemini-embedding-2`.

Tests use deterministic fakes and do not call external APIs.

## Data Model

`corpus/manifest.json` stores public source metadata:

- `doc_id`
- `title`
- `source_url`
- `issuer`
- `revision_date`
- `fetched_at`
- `format`
- `chunk_strategy`
- `track`

`corpus/chunks.jsonl` stores one article per chunk:

- `doc_id`
- `title`
- `article`
- `text`
- `track`
- `source_url`
- `revision_date`

## Evaluation

`eval/golden.yaml` defines 12 questions across tracks A, B, and C.

`eval/run.py` writes JSON with:

- per-case answer/refusal result
- expected references
- citation hit
- refusal correctness
- latency
- aggregate metrics

## Safety

The system prompt forbids using media reports as legal sources. Case-specific penalties, compensation, criminal liability, and unstable news figures are refused. Refusals may list related public-law areas but must not invent amounts or liability conclusions.

## Testing

Implementation follows TDD:

- manifest loading
- article chunk parsing
- deterministic vector retrieval
- citation verification
- refusal classification
- LangGraph answer routing
- eval metrics output

