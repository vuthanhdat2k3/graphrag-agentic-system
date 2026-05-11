"""Ingestion routes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter

from src.ingestion.pipeline import ingest_file_stub

router = APIRouter()


class IngestRequest(BaseModel):
    path: str = Field(..., min_length=1)
    file_type: str = Field(default="pdf")
    dry_run: bool = True


@router.post("/file")
async def ingest_file(body: IngestRequest) -> dict:
    if body.dry_run:
        return {"status": "dry_run", "path": body.path, "file_type": body.file_type}
    # Wire real LightRAG instance when available
    return await ingest_file_stub(lightrag=object(), path=body.path, file_type=body.file_type)
