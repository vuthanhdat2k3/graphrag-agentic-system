"""In-memory BM25 ranking."""

from __future__ import annotations

import pytest

from src.retrieval.bm25 import bm25_memory_index_add, bm25_search


@pytest.mark.asyncio
async def test_bm25_memory_prefers_keyword_overlap() -> None:
    await bm25_memory_index_add("a", "alpha beta graph rag")
    await bm25_memory_index_add("b", "unrelated text about cooking")
    hits = await bm25_search("graph rag", top_k=2)
    assert hits
    assert "graph" in hits[0].text.lower() or "rag" in hits[0].text.lower()
