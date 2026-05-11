"""Agentic orchestrator façade."""

from __future__ import annotations

from src.agents.tools import ToolRegistry, default_tool_registry, reset_tools, set_tools
from src.core.state import AgentState


class AgenticOrchestrator:
    """Compiled LangGraph runner with injectable tool registry."""

    def __init__(self, tools: ToolRegistry | None = None) -> None:
        from src.core.graph import build_agent_graph

        self._tools = tools or default_tool_registry()
        self._graph = build_agent_graph()

    async def run(self, user_query: str) -> AgentState:
        token = set_tools(self._tools)
        try:
            initial: AgentState = {
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
            result = await self._graph.ainvoke(initial)
            return result  # type: ignore[return-value]
        finally:
            reset_tools(token)


__all__ = ["AgenticOrchestrator"]
