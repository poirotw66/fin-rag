from __future__ import annotations

from fastapi import Depends, FastAPI

from .deps import AgentLike, get_agent
from .schemas import AskRequest, AskResponse


def create_app() -> FastAPI:
    app = FastAPI(title="Fin RAG API")

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
            citations=[],
            retrieved=[],
        )

    return app


app = create_app()
