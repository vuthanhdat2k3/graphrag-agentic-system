"""Step-back helper: optional broader query before main retrieval."""

from __future__ import annotations

from src.utils.prompts import load_prompt


async def maybe_step_back(user_query: str) -> str | None:
    """
    Skeleton implementation: loads prompt; production should call an LLM to
    produce a principled step-back question from `step_back.md`.
    """
    _ = load_prompt("step_back.md")
    if len(user_query) < 40:
        return None
    # Heuristic demo: ask for domain context first
    return f"Bối cảnh chung liên quan tới: {user_query[:120]}"


__all__ = ["maybe_step_back"]
