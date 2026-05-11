"""LightRAG wrapper: local / global / hybrid / naive modes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

LightRAGMode = Literal["local", "global", "hybrid", "naive"]


@dataclass
class RetrievalResult:
    chunks: list[str]
    entities: list[dict]
    relations: list[dict]


class LightRAGClient(Protocol):
    async def query(self, q: str, mode: LightRAGMode) -> RetrievalResult: ...


class LightRAGStub:
    """Placeholder until HKUDS LightRAG + Neo4j storage is wired."""

    async def query(self, q: str, mode: LightRAGMode) -> RetrievalResult:
        sample = (
            f"[{mode}] stub context for query: {q[:80]}… "
            "Replace with LightRAG dual-level retrieval + Neo4j backend."
        )
        return RetrievalResult(chunks=[sample], entities=[], relations=[])


lightrag_query_stub: LightRAGClient = LightRAGStub()
