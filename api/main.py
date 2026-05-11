"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from api.middleware import register_middleware
from api.routes import admin, ingest, query


def create_app() -> FastAPI:
    app = FastAPI(title="GraphRAG Agentic API", version="0.1.0")
    register_middleware(app)
    app.include_router(query.router, prefix="/v1/query", tags=["query"])
    app.include_router(ingest.router, prefix="/v1/ingest", tags=["ingest"])
    app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
    return app


app = create_app()
