"""Integration tests for health endpoints that don't require a live database."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def test_health_ok(client: AsyncClient) -> None:
    """`GET /api/v1/health` should return 200 with a confirmation message."""

    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"message": "ok"}


async def test_health_llm_ok(client: AsyncClient) -> None:
    """`GET /api/v1/health/llm` should confirm the Gemini client configures cleanly."""

    response = await client.get("/api/v1/health/llm")
    assert response.status_code == 200
    assert response.json()["message"] == "llm configured"


async def test_health_workflow_ok(client: AsyncClient) -> None:
    """`GET /api/v1/health/workflow` should confirm the LangGraph workflow compiles."""

    response = await client.get("/api/v1/health/workflow")
    assert response.status_code == 200
    assert response.json()["message"] == "workflow ok"
