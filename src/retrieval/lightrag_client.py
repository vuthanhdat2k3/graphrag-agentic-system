"""LightRAG wrapper: local / global / hybrid / naive modes."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal, Protocol

from config.settings import get_settings
from src.ingestion.lightrag_factory import get_lightrag_core
from src.utils.logging import get_logger

LightRAGMode = Literal["local", "global", "hybrid", "naive"]

logger = get_logger(__name__)


@dataclass
class RetrievalResult:
    chunks: list[str]
    entities: list[dict]
    relations: list[dict]


class LightRAGClient(Protocol):
    async def query(self, q: str, mode: LightRAGMode) -> RetrievalResult: ...


class LightRAGStub:
    """Placeholder when LightRAG or credentials are unavailable."""

    async def query(self, q: str, mode: LightRAGMode) -> RetrievalResult:
        sample = (
            f"[{mode}] stub context for query: {q[:80]}… "
            "Install `lightrag`, set OPENAI_API_KEY, and Neo4j if using Neo4JStorage."
        )
        return RetrievalResult(chunks=[sample], entities=[], relations=[])


class HKULightRAGClient:
    """Embedded LightRAG (`aquery` + QueryParam) per HKUDS ProgrammingWithCore.md."""

    async def query(self, q: str, mode: LightRAGMode) -> RetrievalResult:
        rag = await get_lightrag_core()
        if rag is None:
            return await LightRAGStub().query(q, mode)
        try:
            from lightrag import QueryParam
        except ImportError:
            return await LightRAGStub().query(q, mode)

        out = await rag.aquery(
            q,
            param=QueryParam(mode=mode, only_need_context=True),
        )
        text = out if isinstance(out, str) else str(out)
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = parts if parts else ([text.strip()] if text.strip() else [])
        return RetrievalResult(chunks=chunks, entities=[], relations=[])


class CachedLightRAGClient:
    """Optional Redis cache around another LightRAG client."""

    def __init__(self, inner: LightRAGClient) -> None:
        self._inner = inner

    def _key(self, q: str, mode: LightRAGMode) -> str:
        h = hashlib.sha256(f"{mode}:{q}".encode("utf-8")).hexdigest()[:48]
        return f"lightrag:query:{h}"

    async def query(self, q: str, mode: LightRAGMode) -> RetrievalResult:
        s = get_settings()
        if not s.enable_redis_query_cache:
            return await self._inner.query(q, mode)
        try:
            import redis.asyncio as redis_mod
        except ImportError:
            return await self._inner.query(q, mode)

        key = self._key(q, mode)
        client = redis_mod.from_url(s.redis_url, decode_responses=True)
        try:
            cached = await client.get(key)
            if cached:
                raw = json.loads(cached)
                return RetrievalResult(
                    chunks=list(raw.get("chunks", [])),
                    entities=list(raw.get("entities", [])),
                    relations=list(raw.get("relations", [])),
                )
            res = await self._inner.query(q, mode)
            payload = json.dumps(
                {"chunks": res.chunks, "entities": res.entities, "relations": res.relations}
            )
            await client.set(key, payload, ex=s.lightrag_query_cache_ttl_sec)
            return res
        except Exception as exc:  # noqa: BLE001
            logger.warning("lightrag_cache_skip: %s", exc)
            return await self._inner.query(q, mode)
        finally:
            try:
                await client.aclose()
            except Exception:  # noqa: BLE001
                pass


def get_default_lightrag_client() -> LightRAGClient:
    """Default client: HKU core with optional Redis cache."""
    return CachedLightRAGClient(HKULightRAGClient())


lightrag_query_stub: LightRAGClient = LightRAGStub()
