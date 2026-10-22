"""Health check endpoints for liveness/readiness probes and diagnostics."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ai_agents.config.llm import get_gemini_llm
from ai_agents.graph.hiring_graph import get_compiled_hiring_graph
from app.database.session import get_db_session
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=MessageResponse,
    summary="Basic liveness check",
    description="Returns 200 if the API process is up. Does not check any downstream dependency.",
)
async def health() -> MessageResponse:
    """Basic liveness probe.

    Returns:
        A simple confirmation message.
    """

    return MessageResponse(message="ok")


@router.get(
    "/database",
    response_model=MessageResponse,
    summary="Database connectivity check",
    description="Executes a trivial query against PostgreSQL to confirm connectivity.",
)
async def health_database(session: AsyncSession = Depends(get_db_session)) -> MessageResponse:
    """Check that the database is reachable.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A confirmation message if the query succeeds.
    """

    await session.execute(text("SELECT 1"))
    return MessageResponse(message="database ok")


@router.get(
    "/llm",
    response_model=MessageResponse,
    summary="LLM configuration check",
    description="Confirms the Gemini client can be constructed from current settings, "
    "without making a live network call to the model provider.",
)
async def health_llm() -> MessageResponse:
    """Check that the Gemini LLM client is configured correctly.

    Returns:
        A confirmation message if the client can be built.
    """

    get_gemini_llm()
    return MessageResponse(message="llm configured")


@router.get(
    "/workflow",
    response_model=MessageResponse,
    summary="LangGraph workflow compilation check",
    description="Confirms the hiring LangGraph workflow compiles successfully.",
)
async def health_workflow() -> MessageResponse:
    """Check that the hiring LangGraph workflow compiles.

    Returns:
        A confirmation message if the graph compiles.
    """

    get_compiled_hiring_graph()
    return MessageResponse(message="workflow ok")
