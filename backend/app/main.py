"""FastAPI application factory and entrypoint.

Run with: `uvicorn app.main:app --reload`
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.base import Base
from app.database.session import engine
from app.exceptions.handlers import register_exception_handlers
from app.middleware.cors import add_cors_middleware
from app.middleware.csrf import OriginGuardMiddleware
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
import app.models  # noqa: F401 — register ORM tables on Base.metadata

configure_logging()
logger = get_logger(__name__, component="startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup/shutdown resources."""

    logger.info("Application starting up.")
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("SQLite schema is ready.")
    yield
    logger.info("Application shutting down.")
    await engine.dispose()


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""

    settings = get_settings()
    docs_enabled = not settings.is_production

    app = FastAPI(
        title=settings.app_name,
        description="Enterprise hiring platform backend: authentication, job/candidate "
        "management, and an AI-powered LangGraph evaluation workflow.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )

    app.add_middleware(OriginGuardMiddleware)
    add_cors_middleware(app)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.trusted_hosts if settings.trusted_hosts else ["*"],
    )
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "service": "talent-lens-api",
            "health": "/api/v1/health",
            "message": "This is the API, not the website. Open the talent-lens-web URL.",
        }

    return app


app: FastAPI = create_app()
