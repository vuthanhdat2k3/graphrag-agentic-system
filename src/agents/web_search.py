"""Optional web search (SerpApi) for CRAG / orchestrator fallback."""

from __future__ import annotations

import httpx

from config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def serpapi_search(query: str) -> list[str]:
    s = get_settings()
    if not s.serpapi_api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={"engine": "google", "q": query, "api_key": s.serpapi_api_key},
            )
            resp.raise_for_status()
            data = resp.json()
        snippets: list[str] = []
        for key in ("answer_box", "knowledge_graph", "organic_results"):
            block = data.get(key)
            if isinstance(block, dict):
                for field in ("answer", "snippet", "title"):
                    val = block.get(field)
                    if isinstance(val, str) and val.strip():
                        snippets.append(val.strip())
            elif isinstance(block, list):
                for item in block[:5]:
                    if isinstance(item, dict):
                        sn = item.get("snippet") or item.get("title")
                        if isinstance(sn, str) and sn.strip():
                            snippets.append(sn.strip())
        return snippets[:8] or [str(data)[:500]]
    except Exception as exc:  # noqa: BLE001
        logger.warning("serpapi_failed: %s", exc)
        return []


def make_web_search_fn():
    s = get_settings()
    if not s.serpapi_api_key:
        return None

    async def _fn(q: str) -> list[str]:
        return await serpapi_search(q)

    return _fn
