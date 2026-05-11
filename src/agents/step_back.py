"""Step-back helper: optional broader query before main retrieval."""

from __future__ import annotations

from config.settings import get_settings
from src.llm.client import get_orchestrator_chat_client
from src.utils.prompts import load_prompt


async def maybe_step_back(user_query: str) -> str | None:
    load_prompt("step_back.md")
    s = get_settings()
    client = get_orchestrator_chat_client()
    if s.use_llm_step_back and client is not None:
        prompt = (
            f"{load_prompt('step_back.md')}\n\n"
            "User question:\n"
            f"{user_query}\n\n"
            "Respond with ONE short broader retrieval question (no quotes), "
            "or the word SKIP if not needed."
        )
        raw = (await client.complete(prompt, temperature=0.2)).strip()
        if raw.upper() == "SKIP" or not raw:
            return None
        return raw

    if len(user_query) < 40:
        return None
    return f"Bối cảnh chung liên quan tới: {user_query[:120]}"


__all__ = ["maybe_step_back"]
