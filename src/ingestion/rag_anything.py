"""RAG-Anything integration hooks (HKUDS multimodal → LightRAG) — placeholder."""

from __future__ import annotations

from typing import Any, Protocol


class RAGAnythingLike(Protocol):
    async def process_file(self, file_path: str, file_type: str) -> Any: ...


class RAGAnythingPlaceholder:
    """
    Replace with `from raganything import RAGAnything` once dependencies
    are installed. RAG-Anything parses multimodal docs then forwards into
    the LightRAG instance.
    """

    def __init__(self, lightrag: Any) -> None:
        self._lightrag = lightrag

    async def process_file(self, file_path: str, file_type: str) -> dict[str, str]:
        _ = self._lightrag
        return {"status": "stub", "file_path": file_path, "file_type": file_type}
