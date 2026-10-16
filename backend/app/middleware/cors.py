"""CORS middleware configuration factory."""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import get_settings


def add_cors_middleware(app: FastAPI) -> None:
    """Register CORS middleware using env-configured origins.

    Credentials are allowed because the browser sends JWTs from a separate
    frontend origin. Origins are never `*` when credentials are on.
    """

    settings = get_settings()
    origins = settings.cors_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
        expose_headers=["Content-Disposition"],
        max_age=600,
    )
