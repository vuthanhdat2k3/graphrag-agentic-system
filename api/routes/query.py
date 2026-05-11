"""Query routes."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

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


@router.post("/agentic/stream")
async def agentic_query_stream(body: QueryRequest) -> StreamingResponse:
    """Server-Sent Events stream of orchestrator state snapshots (values mode)."""

    async def event_gen():
        orch = AgenticOrchestrator()
        async for snap in orch.run_stream(body.question):
            yield f"data: {json.dumps(snap, default=str)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")
