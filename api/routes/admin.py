"""Admin / health routes."""

from __future__ import annotations

from fastapi import APIRouter

from src.core.graph import graph_config_snapshot

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/graph-config")
async def graph_config() -> dict:
    return graph_config_snapshot()
