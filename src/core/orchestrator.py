"""Agentic orchestrator façade."""

from __future__ import annotations

from collections.abc import AsyncIterator

from src.agents.tools import ToolRegistry, default_tool_registry, reset_tools, set_tools
from src.core.state import AgentState


class AgenticOrchestrator:
    """Compiled LangGraph runner with injectable tool registry."""

    def __init__(self, tools: ToolRegistry | None = None) -> None:
        from src.core.graph import build_agent_graph

        self._tools = tools or default_tool_registry()
        self._graph = build_agent_graph()

    def _initial_state(self, user_query: str) -> AgentState:
        return {
            "user_query": user_query,
            "sub_questions": [],
            "raw_chunks": [],
            "tool_trace": [],
            "verified_chunks": [],
            "crag_confidence": 0.0,
            "crag_has_conflict": False,
            "triggered_web_search": False,
            "loop_count": 0,
        }

    async def run(self, user_query: str) -> AgentState:
        token = set_tools(self._tools)
        try:
            result = await self._graph.ainvoke(self._initial_state(user_query))
            return result  # type: ignore[return-value]
        finally:
            reset_tools(token)

    async def run_stream(self, user_query: str) -> AsyncIterator[dict]:
        """Yield accumulated graph state after each super-step (`stream_mode=values`)."""
        token = set_tools(self._tools)
        try:
            async for chunk in self._graph.astream(
                self._initial_state(user_query),
                stream_mode="values",
            ):
                yield dict(chunk)
        finally:
            reset_tools(token)


__all__ = ["AgenticOrchestrator"]
