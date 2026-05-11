"""Query routes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from src.core.orchestrator import AgenticOrchestrator

router = APIRouter()


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)


class QueryResponse(BaseModel):
    answer: str
    trace: list[dict]


@router.post("/agentic", response_model=QueryResponse)
async def agentic_query(body: QueryRequest) -> QueryResponse:
    orch = AgenticOrchestrator()
    state = await orch.run(body.question)
    return QueryResponse(
        answer=state.get("final_answer", ""),
        trace=state.get("tool_trace", []),
    )
