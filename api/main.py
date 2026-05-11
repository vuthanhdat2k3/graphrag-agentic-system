"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.middleware import register_middleware
from api.routes import admin, ingest, query
from src.ingestion.lightrag_factory import finalize_lightrag_storages


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    yield
    await finalize_lightrag_storages()


def create_app() -> FastAPI:
    app = FastAPI(title="GraphRAG Agentic API", version="0.1.0", lifespan=lifespan)
    register_middleware(app)
    app.include_router(query.router, prefix="/v1/query", tags=["query"])
    app.include_router(ingest.router, prefix="/v1/ingest", tags=["ingest"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
    return app


app = create_app()
