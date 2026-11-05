"""Shared pytest fixtures for unit and integration tests."""

from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-api-key")

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    """Provide an `httpx.AsyncClient` wired directly to the FastAPI ASGI app.

    Returns:
        An `AsyncClient` usable for integration tests without a running server.
    """

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client
