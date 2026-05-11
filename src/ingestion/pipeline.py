"""Plain-text ingestion → LightRAG (`ainsert`). RAG-Anything integration comes later."""

from __future__ import annotations

from pathlib import Path

from config.settings import get_settings
from src.ingestion.lightrag_factory import get_lightrag_core
from src.utils.logging import get_logger

logger = get_logger(__name__)

_TEXT_LIKE = frozenset({"txt", "text", "md", "markdown", "csv"})


def resolve_ingest_path(raw_path: str) -> Path:
    """Resolve path; optionally jail under INGEST_ROOT."""
    p = Path(raw_path).expanduser()
    if not p.is_absolute():
        root = get_settings().ingest_root
        if root is not None:
            p = (Path(root) / p).resolve()
        else:
            p = p.resolve()
    else:
        p = p.resolve()

    root = get_settings().ingest_root
    if root is not None:
        root_res = Path(root).resolve()
        try:
            p.relative_to(root_res)
        except ValueError as e:
            raise PermissionError(f"path must be under INGEST_ROOT ({root_res}): {p}") from e
    return p


async def ingest_text_file(path: str | Path, *, file_label: str | None = None) -> dict[str, str]:
    """
    Read UTF-8 text from disk and insert into LightRAG.

    Returns ``track_id`` from ``ainsert`` for correlation with LightRAG pipelines.
    """
    p = resolve_ingest_path(str(path)) if isinstance(path, str) else Path(path).resolve()
    if not p.is_file():
        return {"status": "error", "message": f"not a file: {p}"}

    rag = await get_lightrag_core()
    if rag is None:
        return {
            "status": "error",
            "message": "LightRAG not available: set OPENAI_API_KEY and install lightrag-hku (see README).",
        }

    ext = p.suffix.lower().lstrip(".") or "txt"
    if ext not in _TEXT_LIKE:
        return {
            "status": "unsupported",
            "message": f"extension '.{ext}' is not plain-text in this build; use {_TEXT_LIKE} or wait for RAG-Anything.",
        }

    text = p.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return {"status": "error", "message": f"empty file: {p}"}

    cite_path = file_label or str(p)
    track_id = await rag.ainsert(text, file_paths=cite_path)
    logger.info("ingest_ok path=%s track_id=%s", p, track_id)
    return {"status": "ok", "path": str(p), "track_id": str(track_id)}


async def ingest_path(path: str, file_type: str | None = None) -> dict[str, str]:
    """
    Dispatch by declared ``file_type`` or path suffix.

    For now only plain-text paths are supported.
    """
    ft = (file_type or "").lower().lstrip(".")
    if ft and ft not in _TEXT_LIKE:
        return {
            "status": "unsupported",
            "message": f"file_type={file_type}: multimodal/RAG-Anything not wired yet.",
        }
    return await ingest_text_file(path)
