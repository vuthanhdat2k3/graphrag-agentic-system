"""LLM-as-judge evaluators (stubs + hook points for real LLM clients)."""

from __future__ import annotations


async def relevance_scores_stub(query: str, chunks: list[str]) -> list[float]:
    """Replace with JSON scorer using `config/prompts/crag.md`."""
    _ = query
    return [0.92 - 0.01 * i for i in range(len(chunks))] or [0.0]


async def consistency_judge_stub(query: str, chunks: list[str]) -> tuple[bool, str | None]:
    _ = query
    if len(chunks) < 2:
        return False, None
    return False, None
