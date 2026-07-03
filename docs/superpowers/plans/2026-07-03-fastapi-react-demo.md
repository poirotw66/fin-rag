# FastAPI React Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a front-end/back-end separated Fin RAG demo with a FastAPI API and a React single-page product-style interface.

**Architecture:** Keep `src/fin_rag` as the core RAG layer, add a thin FastAPI adapter under `apps/api`, and build a React/Vite frontend under `apps/web` that only talks to HTTP endpoints. Deliver the system in slices: API contracts first, then frontend shell, then end-to-end Q&A flow, then demo polish.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, Pydantic, React, Vite, TypeScript, Vitest, Testing Library

---

### Task 1: Add Backend API Skeleton

**Files:**
- Modify: `pyproject.toml`
- Create: `apps/api/__init__.py`
- Create: `apps/api/app.py`
- Create: `apps/api/schemas.py`
- Create: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing health endpoint test**

```python
from fastapi.testclient import TestClient

from apps.api.app import create_app


def test_health_endpoint_returns_ok():
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: import or route failure because `apps/api/app.py` does not exist yet.

- [ ] **Step 3: Add FastAPI dependencies**

```toml
dependencies = [
  "beautifulsoup4>=4.12",
  "fastapi>=0.115",
  "google-genai>=1.0",
  "langgraph>=0.2",
  "numpy>=1.26",
  "pyyaml>=6.0",
  "requests>=2.31",
  "uvicorn>=0.30",
]
```

- [ ] **Step 4: Create the minimal API app**

`apps/api/app.py`

```python
from __future__ import annotations

from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Fin RAG API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: `OK`

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml apps/api/__init__.py apps/api/app.py tests/test_api_app.py
git commit -m "feat: add FastAPI health endpoint"
```

### Task 2: Add `/api/ask` Request And Response Contracts

**Files:**
- Modify: `apps/api/app.py`
- Create: `apps/api/deps.py`
- Modify: `apps/api/schemas.py`
- Modify: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing ask endpoint test**

```python
from fastapi.testclient import TestClient

from apps.api.app import create_app


def test_ask_endpoint_returns_agent_payload():
    app = create_app()
    client = TestClient(app)

    response = client.post("/api/ask", json={"question": "什麼是風險基礎方法？"})

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "什麼是風險基礎方法？"
    assert "answer" in body
    assert "retrieved" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: `404` for `POST /api/ask`

- [ ] **Step 3: Add request and response schemas**

`apps/api/schemas.py`

```python
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
```

- [ ] **Step 4: Add injectable agent dependency and endpoint shell**

`apps/api/deps.py`

```python
from __future__ import annotations

from fin_rag.agent import FinRagAgent


def get_agent() -> FinRagAgent:
    raise NotImplementedError("Wire real agent in Task 3")
```

`apps/api/app.py`

```python
from fastapi import Depends, FastAPI

from .deps import get_agent
from .schemas import AskRequest, AskResponse


@app.post("/api/ask", response_model=AskResponse)
def ask(payload: AskRequest, agent=Depends(get_agent)) -> AskResponse:
    result = agent.answer(payload.question)
    return AskResponse(
        question=payload.question,
        answer=result.answer,
        refused=result.refused,
        citation_hit=result.citation_hit,
        citations=[],
        retrieved=[],
    )
```

- [ ] **Step 5: Run test to verify the shape passes with a stubbed dependency**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: health test still passes, ask test now fails because dependency is not stubbed or payload is incomplete. Update the test with `app.dependency_overrides[get_agent]`.

- [ ] **Step 6: Commit**

```powershell
git add apps/api/app.py apps/api/deps.py apps/api/schemas.py tests/test_api_app.py
git commit -m "feat: add ask endpoint schemas and shell"
```

### Task 3: Wire Real Agent Construction Into FastAPI

**Files:**
- Create: `apps/api/runtime.py`
- Modify: `apps/api/deps.py`
- Modify: `apps/api/app.py`
- Modify: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing service-availability tests**

```python
def test_ask_returns_503_when_api_key_missing():
    ...


def test_ask_returns_503_when_index_missing():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: endpoint returns wrong status because runtime checks are not implemented yet.

- [ ] **Step 3: Add a runtime builder for the real agent**

`apps/api/runtime.py`

```python
from __future__ import annotations

from pathlib import Path

from fin_rag.agent import FinRagAgent
from fin_rag.config import Settings
from fin_rag.gemini import GeminiClient
from fin_rag.retrieve import Retriever

ROOT = Path(__file__).resolve().parents[2]


def build_agent() -> FinRagAgent:
    settings = Settings.from_env()
    if not settings.api_key:
        raise RuntimeError("GEMINI_API_KEY is required")
    index_path = ROOT / "corpus" / "index.jsonl"
    if not index_path.exists():
        raise RuntimeError("corpus/index.jsonl is required")
    client = GeminiClient(settings.api_key, settings.generation_model, settings.embedding_model)
    retriever = Retriever(client=client, index_path=str(index_path))
    return FinRagAgent(client=client, retrieve=retriever.retrieve)
```

- [ ] **Step 4: Convert runtime failures into HTTP 503**

`apps/api/deps.py`

```python
from fastapi import HTTPException

from .runtime import build_agent


def get_agent():
    try:
        return build_agent()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: `OK`

- [ ] **Step 6: Commit**

```powershell
git add apps/api/runtime.py apps/api/deps.py apps/api/app.py tests/test_api_app.py
git commit -m "feat: wire real Fin RAG agent into FastAPI"
```

### Task 4: Return Full Ask Payload Including Citations And Retrieved Chunks

**Files:**
- Modify: `apps/api/app.py`
- Modify: `apps/api/schemas.py`
- Modify: `tests/test_api_app.py`

- [ ] **Step 1: Write the failing payload-detail test**

```python
def test_ask_endpoint_returns_citations_and_retrieved_chunks():
    ...
    assert body["citations"][0]["doc_id"] == "aml-finst"
    assert body["retrieved"][0]["score"] == 0.9
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: citations or retrieved fields are empty.

- [ ] **Step 3: Serialize the `AgentResult` data**

`apps/api/app.py`

```python
def _build_citations(result) -> list[CitationResponse]:
    seen = set()
    citations = []
    for item in result.retrieved:
        key = (item.chunk.doc_id, item.chunk.article, item.chunk.title)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            CitationResponse(
                doc_id=item.chunk.doc_id,
                article=item.chunk.article,
                title=item.chunk.title,
            )
        )
    return citations
```

and:

```python
retrieved = [
    RetrievedChunkResponse(
        doc_id=item.chunk.doc_id,
        title=item.chunk.title,
        article=item.chunk.article,
        text=item.chunk.text,
        score=round(item.score, 4),
    )
    for item in result.retrieved
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
python -m unittest discover -s tests -p test_api_app.py
```

Expected: `OK`

- [ ] **Step 5: Commit**

```powershell
git add apps/api/app.py apps/api/schemas.py tests/test_api_app.py
git commit -m "feat: return full ask payload from API"
```

### Task 5: Scaffold React Vite Frontend

**Files:**
- Create: `apps/web/package.json`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/index.html`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/styles.css`
- Create: `apps/web/src/api.ts`
- Create: `apps/web/src/types.ts`

- [ ] **Step 1: Write the failing frontend smoke test**

`apps/web/src/App.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders product heading", () => {
  render(<App />);
  expect(screen.getByText(/Fin RAG/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd apps/web
npm test -- --run
```

Expected: project files or test runner are missing.

- [ ] **Step 3: Add minimal Vite React app structure**

`apps/web/package.json`

```json
{
  "name": "fin-rag-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest"
  }
}
```

`apps/web/src/App.tsx`

```tsx
export default function App() {
  return (
    <main>
      <h1>Fin RAG</h1>
      <p>Public financial regulation assistant.</p>
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
cd apps/web
npm test -- --run
```

Expected: `PASS`

- [ ] **Step 5: Commit**

```powershell
git add apps/web
git commit -m "feat: scaffold React Vite demo app"
```

### Task 6: Build The Single-Page Demo Flow

**Files:**
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/api.ts`
- Modify: `apps/web/src/types.ts`
- Modify: `apps/web/src/styles.css`
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: Write the failing interaction tests**

```tsx
test("submits a question and renders answer details", async () => {
  render(<App />);
  await user.type(screen.getByLabelText(/question/i), "什麼是風險基礎方法？");
  await user.click(screen.getByRole("button", { name: /ask/i }));
  expect(await screen.findByText(/Answer/i)).toBeInTheDocument();
  expect(await screen.findByText(/Citations/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
cd apps/web
npm test -- --run
```

Expected: form controls or request flow do not exist yet.

- [ ] **Step 3: Add typed API client**

`apps/web/src/api.ts`

```ts
export async function askQuestion(question: string) {
  const response = await fetch("/api/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(payload.detail ?? "Request failed");
  }
  return response.json();
}
```

- [ ] **Step 4: Implement the page sections**

`apps/web/src/App.tsx`

```tsx
export default function App() {
  return (
    <main className="page">
      <section className="hero">{/* heading, subtitle, form */}</section>
      <section className="answer-card">{/* answer or refusal */}</section>
      <section className="citations-card">{/* citations */}</section>
      <details className="retrieved-card">{/* retrieved chunks */}</details>
    </main>
  );
}
```

- [ ] **Step 5: Add branded product-style CSS**

`apps/web/src/styles.css`

```css
:root {
  --bg: #f3efe5;
  --surface: #fffdf8;
  --ink: #1e2a25;
  --accent: #0d5c46;
  --muted: #6f7b74;
}
```

and continue with card, input, button, and layout styles that support desktop and mobile.

- [ ] **Step 6: Run tests to verify they pass**

Run:

```powershell
cd apps/web
npm test -- --run
```

Expected: `PASS`

- [ ] **Step 7: Commit**

```powershell
git add apps/web/src
git commit -m "feat: build single-page Fin RAG demo UI"
```

### Task 7: Connect Frontend To Backend In Local Development

**Files:**
- Modify: `apps/web/vite.config.ts`
- Modify: `apps/api/app.py`
- Create: `apps/api/README.md`

- [ ] **Step 1: Write the failing integration note or proxy expectation test**

Document the expected local behavior:

```text
Vite serves the frontend on one port and proxies /api to FastAPI on another port.
```

- [ ] **Step 2: Add development proxy configuration**

`apps/web/vite.config.ts`

```ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
```

- [ ] **Step 3: Add backend CORS configuration**

`apps/api/app.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 4: Document how to run both apps**

`apps/api/README.md`

```md
Run API: `uvicorn apps.api.app:app --reload`
Run web: `npm run dev`
```

- [ ] **Step 5: Verify local startup**

Run:

```powershell
uvicorn apps.api.app:app --reload
cd apps/web
npm run dev
```

Expected: frontend loads, `/api/health` reachable through proxy.

- [ ] **Step 6: Commit**

```powershell
git add apps/web/vite.config.ts apps/api/app.py apps/api/README.md
git commit -m "chore: wire local FastAPI and Vite development flow"
```

### Task 8: Final Verification And Demo Readiness

**Files:**
- Modify: `README.md`
- Verify: `tests/`, `apps/api`, `apps/web`

- [ ] **Step 1: Add README demo instructions**

```md
## Demo App

Backend:
`uvicorn apps.api.app:app --reload`

Frontend:
`cd apps/web && npm run dev`
```

- [ ] **Step 2: Run backend tests**

Run:

```powershell
python run_tests.py
```

Expected: `OK`

- [ ] **Step 3: Run frontend tests**

Run:

```powershell
cd apps/web
npm test -- --run
```

Expected: `PASS`

- [ ] **Step 4: Run production frontend build**

Run:

```powershell
cd apps/web
npm run build
```

Expected: build completes successfully.

- [ ] **Step 5: Do a manual end-to-end demo check**

Run:

```powershell
uvicorn apps.api.app:app --reload
cd apps/web
npm run dev
```

Expected:

- page loads
- question submits successfully
- answer card renders
- citations render
- retrieved chunks expand

- [ ] **Step 6: Commit**

```powershell
git add README.md
git commit -m "docs: add demo app run instructions"
```
