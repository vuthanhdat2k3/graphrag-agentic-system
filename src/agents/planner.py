"""LLM-assisted decomposition and routing (optional)."""

from __future__ import annotations

from typing import Any

from config.settings import get_settings
from src.llm.client import get_orchestrator_chat_client
from src.llm.json_utils import parse_json_object
from src.utils.prompts import load_prompt


async def llm_decompose(user_query: str) -> dict[str, Any]:
    client = get_orchestrator_chat_client()
    if not get_settings().use_llm_planner or client is None:
        return {}
    guide = load_prompt("decomposition.md")
    prompt = (
        f"{guide}\n\nUser question:\n{user_query}\n\n"
        'Return ONLY JSON: {{"sub_questions": [string, ...]}} '
        "If a single question is enough, return it as the only element."
    )
    raw = await client.complete(prompt, temperature=0.1)
    try:
        obj = parse_json_object(raw)
        subs = obj.get("sub_questions")
        if isinstance(subs, list) and subs:
            return {"sub_questions": [str(x) for x in subs]}
    except Exception:  # noqa: BLE001
        pass
    return {}


async def llm_route(user_query: str, loop: int) -> dict[str, Any]:
    client = get_orchestrator_chat_client()
    if not get_settings().use_llm_planner or client is None:
        return {}
    orch = load_prompt("orchestrator.md")
    prompt = (
        f"{orch}\n\nLoop: {loop}\nUser question:\n{user_query}\n\n"
        'Return ONLY JSON: {{"route_tool": "lightrag_query"|"bm25_search", '
        '"lightrag_mode": "local"|"global"|"hybrid"|"naive"}}'
    )
    raw = await client.complete(prompt, temperature=0.0)
    try:
        obj = parse_json_object(raw)
        route = obj.get("route_tool")
        mode = obj.get("lightrag_mode")
        out: dict[str, Any] = {}
        if route in ("lightrag_query", "bm25_search"):
            out["route_tool"] = route
        if mode in ("local", "global", "hybrid", "naive"):
            out["lightrag_mode"] = mode
        return out
    except Exception:  # noqa: BLE001
        return {}
