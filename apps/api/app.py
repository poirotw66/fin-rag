from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import AgentLike, get_agent
from .schemas import AskRequest, AskResponse, CitationResponse, RetrievedChunkResponse


def _build_citations(result) -> list[CitationResponse]:
    seen: set[tuple[str, str, str]] = set()
    citations: list[CitationResponse] = []
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


def _build_retrieved(result) -> list[RetrievedChunkResponse]:
    return [
        RetrievedChunkResponse(
            doc_id=item.chunk.doc_id,
            title=item.chunk.title,
            article=item.chunk.article,
            text=item.chunk.text,
            score=round(item.score, 4),
        )
        for item in result.retrieved
    ]


def create_app() -> FastAPI:
    app = FastAPI(title="Fin RAG API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/ask", response_model=AskResponse)
    def ask(payload: AskRequest, agent: AgentLike = Depends(get_agent)) -> AskResponse:
        result = agent.answer(payload.question)
        return AskResponse(
            question=payload.question,
            answer=result.answer,
            refused=result.refused,
            citation_hit=result.citation_hit,
            citations=_build_citations(result),
            retrieved=_build_retrieved(result),
        )

    return app


app = create_app()
