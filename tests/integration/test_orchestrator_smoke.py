"""Smoke: orchestrator runs with stub tools."""

from __future__ import annotations

import pytest

from src.core.orchestrator import AgenticOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_smoke() -> None:
    orch = AgenticOrchestrator()
    state = await orch.run("What is GraphRAG?")
    assert "final_answer" in state
    assert state.get("tool_trace")
