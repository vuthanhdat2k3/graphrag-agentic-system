"""Shared graph state for the orchestrator workflow."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from typing_extensions import NotRequired

LightRAGMode = Literal["local", "global", "hybrid", "naive"]


class AgentState(TypedDict, total=False):
    """End-to-end state for one user question."""

    user_query: str
    sub_questions: list[str]
    step_back_query: NotRequired[str | None]
    plan_notes: NotRequired[str]
    route_tool: NotRequired[str]
    lightrag_mode: NotRequired[LightRAGMode]
    raw_chunks: list[str]
    tool_trace: list[dict[str, Any]]
    verified_chunks: list[str]
    crag_confidence: float
    crag_has_conflict: bool
    triggered_web_search: bool
    loop_count: int
    stop_reason: NotRequired[str]
    final_answer: NotRequired[str]
