"""Shared Pydantic schemas used across multiple route modules."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    """Standard error envelope returned by global exception handlers."""

    error: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable error message.")
    details: dict | None = Field(default=None, description="Optional structured error details.")


class PaginationParams(BaseModel):
    """Common pagination query parameters."""

    offset: int = Field(default=0, ge=0, description="Number of records to skip.")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of records to return.")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated list response wrapper."""

    items: list[T] = Field(..., description="The page of results.")
    total: int = Field(..., description="Total number of matching records, across all pages.")
    offset: int = Field(..., description="Offset used for this page.")
    limit: int = Field(..., description="Limit used for this page.")


class MessageResponse(BaseModel):
    """Simple acknowledgement response for actions with no return payload."""

    message: str = Field(..., description="Human-readable confirmation message.")
