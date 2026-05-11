"""Cross-cutting FastAPI middleware."""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
