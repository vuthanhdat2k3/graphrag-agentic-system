"""BM25 sparse retrieval — stub (Elasticsearch / Whoosh to be implemented)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BM25Document:
    text: str
    source: str
    score: float


async def bm25_search_stub(query: str, top_k: int = 10) -> list[BM25Document]:
    _ = top_k
    return [
        BM25Document(
            text=f"BM25 stub hit for: {query[:120]}",
            source="stub_index",
            score=1.0,
        )
    ]
