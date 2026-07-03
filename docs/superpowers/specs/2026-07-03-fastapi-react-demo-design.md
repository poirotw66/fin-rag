# FastAPI + React Demo Design

## Goal

Build a front-end/back-end separated demo system for Fin RAG using FastAPI and React. The demo should feel like a polished product, centered on a single-page financial regulation Q&A experience.

## Product Direction

The primary experience is a clean public-facing question-and-answer page. It should feel like an AI product rather than an internal admin tool. At the same time, it should preserve a small amount of analyst-friendly transparency through citations and expandable retrieval details.

The demo should combine:

- the simplicity of a single-page Q&A assistant
- the trust signals of legal citations
- light technical transparency for retrieval evidence

## Architecture

The system will be split into three layers:

### 1. Core RAG Layer

Existing logic in `src/fin_rag` remains the source of truth for:

- retrieval
- Gemini calls
- refusal logic
- citation checking
- evaluation

This layer should stay reusable by CLI, API, and future batch or UI integrations.

### 2. FastAPI Backend

A new FastAPI app will act as a thin HTTP layer over `FinRagAgent`. It should be responsible for:

- request validation
- response serialization
- startup-time environment and index checks
- HTTP error handling
- CORS configuration for local front-end development

The backend should not duplicate RAG logic. It should only adapt the existing agent into stable API contracts.

### 3. React Frontend

A React app will provide the single-page demo interface. It should be responsible for:

- question input flow
- loading and error states
- answer presentation
- citation display
- expandable retrieval details
- lightweight system status display

The frontend should consume the API only through HTTP and should not depend on Python internals.

## API Design

Version one needs only two endpoints.

### `POST /api/ask`

Purpose: accept a user question and return a full machine-readable RAG result.

Request body:

```json
{
  "question": "客戶身分確認 CDD 要做哪些事？"
}
```

Response body:

```json
{
  "question": "客戶身分確認 CDD 要做哪些事？",
  "answer": "....",
  "refused": false,
  "citation_hit": true,
  "citations": [
    {
      "doc_id": "aml-finst",
      "article": "第 7 條",
      "title": "金融機構防制洗錢辦法"
    }
  ],
  "retrieved": [
    {
      "doc_id": "aml-finst",
      "title": "金融機構防制洗錢辦法",
      "article": "第 7 條",
      "text": "金融機構應進行客戶身分確認...",
      "score": 0.91
    }
  ]
}
```

### `GET /api/health`

Purpose: let the frontend confirm the backend is alive and ready before a demo.

Response:

```json
{
  "status": "ok"
}
```

## Error Handling

The first version only needs a small set of predictable errors:

- `400 Bad Request`: empty or invalid question input
- `503 Service Unavailable`: missing `GEMINI_API_KEY` or retrieval index not ready
- `500 Internal Server Error`: unexpected backend failure such as Gemini or runtime errors

Error responses should be JSON and should include a short readable message for the frontend.

## Frontend Page Design

The UI should be a single-page application with one primary workflow.

### 1. Hero And Input Area

The top section should present:

- a clear product title
- a short subtitle explaining this is a public financial regulation assistant
- one prominent input box
- one submit button

This section should immediately communicate confidence and simplicity.

### 2. Answer Card

The answer area is the primary output surface.

- In normal cases, it shows the generated answer.
- In refusal cases, it shows a styled refusal state that feels deliberate and trustworthy rather than error-like.

### 3. Citations Card

This section should list the references used in the response.

Each citation should show:

- title
- article
- doc_id

This is the main trust-building element in the page.

### 4. Retrieved Chunks Disclosure

Retrieved chunk details should be available but not visually dominant.

- default state: collapsed
- expanded state: show source, score, and snippet

This keeps the page product-like while still allowing analyst inspection during demos.

### 5. System Status Area

A small status element should show lightweight environment information such as:

- backend health
- request state
- optionally current configured generation model

This should stay secondary and must not crowd the main experience.

## Interaction Flow

### Initial State

The page shows the hero area and a short hint or example question.

### Loading State

On submit:

- disable the submit button
- show a loading state in the result area
- preserve the entered question

### Success State

On success:

- show the answer card
- show citations
- enable the retrieved chunk disclosure

### Failure State

On API failure:

- show a readable inline error message
- avoid disruptive alert dialogs
- allow quick retry

## Repository Structure

The repo should evolve into a split but still cohesive layout:

```text
src/fin_rag/            Core RAG logic
scripts/                Existing CLI entry points
apps/api/               FastAPI backend app
apps/web/               React frontend app
docs/superpowers/specs/ Design docs
docs/superpowers/plans/ Implementation plans
```

`apps/api` should depend on `src/fin_rag`, while `apps/web` should depend only on HTTP contracts.

## Testing Strategy

The implementation should be test-driven and split by boundary:

- backend schema and endpoint tests
- frontend component and request-state tests
- minimal integration test for `POST /api/ask`

The existing `run_tests.py` should continue to verify Python-side behavior. Frontend tests can be introduced separately under the web app.

## Scope Boundaries

This first demo does not need:

- authentication
- persistent chat history
- streaming responses
- multi-page frontend routing
- eval dashboard integration

Those can come later after the single-page experience is stable.

## Recommended First Implementation Slice

The first delivery slice should be:

1. FastAPI `health` and `ask` endpoints
2. React single-page input and answer flow
3. citations section
4. collapsible retrieved chunks section
5. basic branded styling

This slice is enough for a convincing end-to-end demo without overbuilding.
