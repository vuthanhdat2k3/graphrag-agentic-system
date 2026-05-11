"""Lazy singleton LightRAG core (HKUDS). Requires optional `lightrag` + OpenAI env."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from config.settings import get_settings

_rag: Any = None
_lock = asyncio.Lock()


async def get_lightrag_core() -> Any | None:
    """
    Return initialized LightRAG instance or None if dependency / API key missing.

    See: https://github.com/HKUDS/LightRAG/blob/main/docs/ProgramingWithCore.md
    """
    global _rag
    async with _lock:
        if _rag is not None:
            return _rag
        try:
            from lightrag import LightRAG
            from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed
        except ImportError:
            return None

        s = get_settings()
        if not s.openai_api_key:
            return None

        wd = Path(s.lightrag_working_dir)
        wd.mkdir(parents=True, exist_ok=True)

        instance = LightRAG(
            working_dir=str(wd),
            embedding_func=openai_embed,
            llm_model_func=gpt_4o_mini_complete,
            graph_storage=s.lightrag_graph_storage,
        )
        await instance.initialize_storages()
        _rag = instance
        return _rag


async def finalize_lightrag_storages() -> None:
    """Call on app shutdown."""
    global _rag
    async with _lock:
        if _rag is None:
            return
        try:
            await _rag.finalize_storages()
        except Exception:
            pass
        finally:
            _rag = None


def reset_lightrag_for_tests() -> None:
    """Clear singleton (sync, tests only)."""
    global _rag
    _rag = None
