"""Tool registry + defaults (LightRAG, Cypher, BM25, CRAG, web)."""

from __future__ import annotations

import contextvars
from dataclasses import dataclass
from typing import Protocol

from src.agents.web_search import make_web_search_fn
from src.crag.module import CRAGModule, CRAGResult
from src.llm.client import get_crag_chat_client
from src.retrieval.bm25 import BM25Document, bm25_search
from src.retrieval.cypher import CypherClient, make_cypher_client
from src.retrieval.lightrag_client import LightRAGClient, LightRAGMode, RetrievalResult, get_default_lightrag_client

_current_tools: contextvars.ContextVar["ToolRegistry | None"] = contextvars.ContextVar(
    "tool_registry",
    default=None,
)


class WebSearchFn(Protocol):
    async def __call__(self, query: str) -> list[str]: ...


@dataclass
class ToolRegistry:
    lightrag: LightRAGClient
    cypher: CypherClient
    crag: CRAGModule

    async def lightrag_query(self, query: str, mode: LightRAGMode) -> RetrievalResult:
        return await self.lightrag.query(query, mode)

    async def bm25_search(self, query: str, top_k: int = 10) -> list[BM25Document]:
        return await bm25_search(query, top_k=top_k)

    async def crag_verify(self, query: str, chunks: list[str]) -> CRAGResult:
        return await self.crag.evaluate(query, chunks)

    web_search: WebSearchFn | None = None

    async def cypher_query(self, cypher: str) -> list[dict]:
        return await self.cypher.run(cypher)


def default_tool_registry() -> ToolRegistry:
    return ToolRegistry(
        lightrag=get_default_lightrag_client(),
        cypher=make_cypher_client(),
        crag=CRAGModule(
            llm=get_crag_chat_client(),
            web_search_fn=make_web_search_fn(),
        ),
        web_search=make_web_search_fn(),
    )


def get_tools() -> ToolRegistry:
    reg = _current_tools.get()
    if reg is None:
        return default_tool_registry()
    return reg


def set_tools(registry: ToolRegistry) -> contextvars.Token:
    return _current_tools.set(registry)


def reset_tools(token: contextvars.Token) -> None:
    _current_tools.reset(token)
