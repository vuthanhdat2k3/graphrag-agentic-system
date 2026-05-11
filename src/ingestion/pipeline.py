"""End-to-end ingestion: parse → graph build → indexes (wired incrementally)."""

from __future__ import annotations

from src.ingestion.rag_anything import RAGAnythingPlaceholder


async def ingest_file_stub(lightrag: object, path: str, file_type: str) -> dict[str, str]:
    rag_anything = RAGAnythingPlaceholder(lightrag)
    return await rag_anything.process_file(path, file_type)
