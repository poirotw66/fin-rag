# Fin RAG

CLI-first financial regulation Agentic RAG MVP built on public MOJ and FSC sources.

## Status

This repository is currently at a working MVP stage.

- Public-law corpus ingestion and chunking are in place.
- Gemini embeddings and generation are wired into the runtime flow.
- Retrieval uses a local JSONL vector index.
- The answer flow runs through `classify -> retrieve -> generate -> citation_check -> final/refusal`.
- LangGraph is used when installed, with a sequential fallback for constrained environments.
- Golden-set evaluation and automated tests are passing.

Latest verified local results:

- `python run_tests.py`: 10/10 tests passed
- `eval/last_report.json`: `citation_hit_rate = 1.0`
- `eval/last_report.json`: `refusal_accuracy = 1.0`
- `eval/last_report.json`: `expected_refs_retrieved_rate = 1.0`

## What It Does

The project builds a small regulatory corpus from public legal text, splits it into article-level chunks, embeds the chunks with Gemini, retrieves top-k references for a question, and generates a cited answer.

The system is designed to refuse:

- case-specific penalties
- compensation or liability conclusions
- criminal-liability determinations
- unstable news or market-figure claims

This is not legal advice.

## Project Layout

```text
src/fin_rag/         Core package
apps/api/            FastAPI adapter
apps/web/            React demo UI
scripts/             CLI entry scripts
corpus/              Manifest, raw sources, chunks, and index
eval/                Golden set, runner, and last report
tests/               Unit and integration tests
docs/                Design notes and implementation plan
```

## Setup

Requirements:

- Python 3.11+
- Gemini API key

Create `.env` in the project root:

```text
GEMINI_API_KEY=...
FIN_RAG_GENERATION_MODEL=gemini-2.5-flash
FIN_RAG_EMBEDDING_MODEL=gemini-embedding-2
```

Install dependencies with your preferred environment manager, then run the commands below from the repo root.

## Commands

Build chunks from the corpus:

```powershell
python scripts/chunk_by_article.py
```

Build the retrieval index:

```powershell
python scripts/build_index.py
```

Ask a question:

```powershell
python scripts/ask.py "What does CDD require?"
```

Run golden-set evaluation:

```powershell
python eval/run.py
```

Run the full test suite:

```powershell
python run_tests.py
```

## Demo App

Backend:

```bash
uvicorn apps.api.app:app --reload
```

Frontend:

```bash
cd apps/web && npm run dev
```

Vite serves the UI on port 5173 and proxies `/api` to FastAPI on port 8000. Set `GEMINI_API_KEY` in `.env` before submitting questions.

## Corpus Scope

Current MVP tracks:

- Track A: AML, CDD, and internal-control compliance
- Track B: investment-trust related-party and material-event compliance
- Track C: refusal behavior for penalties, compensation, and unstable claims

Media reports are intentionally excluded from retrieval and cannot be used as legal citations.

See [corpus/README.md](corpus/README.md) for corpus-specific notes.

## Verification

This workspace has already been verified with:

- real `langgraph`
- real `google-genai`
- Gemini generation
- Gemini embeddings

The evaluation runner writes a JSON report to `eval/last_report.json`.

## Safety Notes

Answers must cite retrieved public legal text. If the generated answer does not ground itself in the retrieved references, the agent falls back to refusal instead of returning an unsupported answer.
