"""Ingestion routes."""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from config.settings import get_settings
from src.ingestion.pipeline import ingest_path

router = APIRouter()


class IngestRequest(BaseModel):
    path: str = Field(..., min_length=1, description="Path on server; if relative, joined with INGEST_ROOT when set.")
    file_type: str = Field(default="txt", description="For text: txt, md, csv, …")
    dry_run: bool = Field(default=True)


@router.post("/file")
async def ingest_file(body: IngestRequest) -> dict:
    if body.dry_run:
        root = get_settings().ingest_root
        return {
            "status": "dry_run",
            "path": body.path,
            "file_type": body.file_type,
            "ingest_root": str(root) if root else None,
        }
    result = await ingest_path(body.path, body.file_type)
    status = result.get("status", "error")
    if status == "ok":
        return result
    code = 415 if status == "unsupported" else 400
    raise HTTPException(status_code=code, detail=result.get("message", result))
