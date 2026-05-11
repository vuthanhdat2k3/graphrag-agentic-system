"""LLM-as-judge evaluators with deterministic fallback when no API key."""

from __future__ import annotations

from typing import Any

from src.llm.client import ChatClient
from src.llm.json_utils import parse_json_array, parse_json_object
from src.utils.prompts import load_prompt


async def relevance_scores(
    query: str,
    chunks: list[str],
    llm: ChatClient | None,
) -> list[float]:
    if not chunks:
        return []
    if llm is None:
        return [max(0.0, 0.92 - 0.05 * i) for i in range(len(chunks))]

    header = load_prompt("crag.md")
    numbered = "\n".join(f"[{i}] {c[:800]}" for i, c in enumerate(chunks))
    prompt = (
        f"{header}\n\nQuery: {query}\n\nChunks:\n{numbered}\n\n"
        "Return ONLY a JSON array of floats, same length and order as chunks, "
        "scores between 0 and 1 for relevance."
    )
    raw = await llm.complete(prompt, temperature=0.0)
    try:
        arr = parse_json_array(raw)
        out = [float(x) for x in arr]
        if len(out) != len(chunks):
            raise ValueError("length mismatch")
        return out
    except Exception:  # noqa: BLE001
        return [max(0.0, 0.85 - 0.05 * i) for i in range(len(chunks))]


async def consistency_judge(
    query: str,
    chunks: list[str],
    llm: ChatClient | None,
) -> tuple[bool, str | None]:
    if len(chunks) < 2:
        return False, None
    if llm is None:
        return False, None

    header = load_prompt("crag.md")
    numbered = "\n".join(f"[{i}] {c[:500]}" for i, c in enumerate(chunks))
    prompt = (
        f"{header}\n\nQuery: {query}\n\nChunks:\n{numbered}\n\n"
        'Return ONLY JSON: {{"conflict": true|false, "description": string|null}}'
    )
    raw = await llm.complete(prompt, temperature=0.0)
    try:
        obj: dict[str, Any] = parse_json_object(raw)
        return bool(obj.get("conflict")), obj.get("description")
    except Exception:  # noqa: BLE001
        return False, None
