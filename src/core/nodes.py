"""LangGraph node callables (Plan → Route → Act → Verify → Stop)."""

from __future__ import annotations

import uuid
from typing import Any

from config.settings import get_settings
from src.agents.step_back import maybe_step_back
from src.agents.tools import get_tools
from src.core.state import AgentState
from src.utils.logging import get_logger
from src.utils.prompts import load_prompt

logger = get_logger(__name__)


def _trace_append(state: AgentState, step: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    entry: dict[str, Any] = {"id": str(uuid.uuid4())[:8], "step": step, **payload}
    prior = list(state.get("tool_trace", []))
    prior.append(entry)
    return prior


async def node_plan(state: AgentState) -> dict[str, Any]:
    load_prompt("orchestrator.md")
    user_q = state["user_query"]
    step_back = await maybe_step_back(user_q)
    subqs = [user_q] if not state.get("sub_questions") else state["sub_questions"]
    return {
        "sub_questions": subqs,
        "step_back_query": step_back,
        "plan_notes": "full LLM planner: decomposition.md + orchestrator.md",
        "tool_trace": _trace_append(state, "plan", {"sub_questions": subqs, "step_back": step_back}),
    }


async def node_route(state: AgentState) -> dict[str, Any]:
    q = state["user_query"]
    mode = "hybrid"
    if any(k in q.lower() for k in ("điều khoản", "mục", "document", "file")):
        route = "bm25_search"
    else:
        route = "lightrag_query"
    loop = state.get("loop_count", 0) + 1
    return {
        "route_tool": route,
        "lightrag_mode": mode,  # type: ignore[typeddict-item]
        "loop_count": loop,
        "tool_trace": _trace_append(
            state,
            "route",
            {"tool": route, "lightrag_mode": mode, "loop": loop},
        ),
    }


async def node_act(state: AgentState) -> dict[str, Any]:
    tools = get_tools()
    route = state.get("route_tool", "lightrag_query")
    q = state["user_query"]
    if state.get("step_back_query") and state.get("loop_count", 0) <= 1:
        q = f"{state['step_back_query']} / {q}"
    chunks: list[str] = []
    if route == "lightrag_query":
        mode = state.get("lightrag_mode", "hybrid")
        res = await tools.lightrag.query(q, mode)
        chunks = res.chunks
    elif route == "bm25_search":
        docs = await tools.bm25_search(q, top_k=10)
        chunks = [d.text for d in docs]
    else:
        res = await tools.lightrag.query(q, "hybrid")
        chunks = res.chunks
    return {
        "raw_chunks": chunks,
        "tool_trace": _trace_append(state, "act", {"route": route, "n_chunks": len(chunks)}),
    }


async def node_verify(state: AgentState) -> dict[str, Any]:
    tools = get_tools()
    chunks = state.get("raw_chunks", [])
    result = await tools.crag_verify(state["user_query"], chunks)
    trace = _trace_append(
        state,
        "verify",
        {
            "confidence": result.confidence_score,
            "has_conflict": result.has_conflict,
            "web": result.triggered_web_search,
        },
    )
    out: dict[str, Any] = {
        "verified_chunks": result.verified_chunks,
        "crag_confidence": result.confidence_score,
        "crag_has_conflict": result.has_conflict,
        "triggered_web_search": result.triggered_web_search,
        "tool_trace": trace,
    }
    settings = get_settings()
    if result.confidence_score < settings.crag_expand_threshold and tools.web_search is not None:
        extra = await tools.web_search(state["user_query"])
        out["verified_chunks"] = result.verified_chunks + extra
        out["triggered_web_search"] = True
    return out


async def node_stop(state: AgentState) -> dict[str, Any]:
    settings = get_settings()
    reason = "max_loops_or_low_confidence"
    if state.get("crag_confidence", 0) >= settings.crag_high_confidence:
        reason = "high_confidence"
    elif state.get("loop_count", 0) >= settings.max_orchestrator_loops:
        reason = "max_loops"
    answer = "\n\n".join(state.get("verified_chunks", [])) or "(no context)"
    logger.info("orchestrator_stop", extra={"reason": reason})
    return {
        "stop_reason": reason,
        "final_answer": answer,
        "tool_trace": _trace_append(state, "stop", {"reason": reason}),
    }


def should_continue(state: AgentState) -> str:
    settings = get_settings()
    if state.get("stop_reason"):
        return "stop"
    if state.get("crag_confidence", 0) >= settings.crag_high_confidence:
        return "stop"
    if state.get("loop_count", 0) >= settings.max_orchestrator_loops:
        return "stop"
    return "continue"
