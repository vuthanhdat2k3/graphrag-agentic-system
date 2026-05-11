"""LangGraph workflow definition."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from config.settings import get_settings
from src.core.nodes import (
    node_act,
    node_plan,
    node_route,
    node_stop,
    node_verify,
    should_continue,
)
from src.core.state import AgentState


def build_agent_graph():
    graph = StateGraph(AgentState)
    graph.add_node("plan", node_plan)
    graph.add_node("route", node_route)
    graph.add_node("act", node_act)
    graph.add_node("verify", node_verify)
    graph.add_node("stop", node_stop)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "route")
    graph.add_edge("route", "act")
    graph.add_edge("act", "verify")
    graph.add_conditional_edges(
        "verify",
        should_continue,
        {"continue": "route", "stop": "stop"},
    )
    graph.add_edge("stop", END)
    return graph.compile()


def graph_config_snapshot() -> dict[str, Any]:
    s = get_settings()
    return {
        "max_orchestrator_loops": s.max_orchestrator_loops,
        "crag_high_confidence": s.crag_high_confidence,
        "crag_expand_threshold": s.crag_expand_threshold,
    }
