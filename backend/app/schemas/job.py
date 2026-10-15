"""Pydantic schemas for job resources."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import JobStatus


class JobCreate(BaseModel):
    """Request body for `POST /jobs`."""

    title: str = Field(..., min_length=1, max_length=255, examples=["Senior Backend Engineer"])
    description: str = Field(..., min_length=1, examples=["We are looking for..."])
    requirements: str = Field(..., min_length=1, examples=["5+ years Python, PostgreSQL, AWS"])
    status: JobStatus = Field(default=JobStatus.DRAFT)


class ExtractRequirementsRequest(BaseModel):
    """Request body for `POST /jobs/{id}/extract-requirements`."""

    apply: bool = False


class ExtractRequirementsResponse(BaseModel):
    """Structured requirements extracted from a job posting."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience: str = ""
    qualifications: list[str] = Field(default_factory=list)
    applied: bool = False


class JobUpdate(BaseModel):
    """Request body for `PUT /jobs/{id}`. All fields optional (partial update)."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    requirements: str | None = Field(default=None, min_length=1)
    status: JobStatus | None = None


class JobRead(BaseModel):
    """Public representation of a job posting."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    requirements: str
    extracted_requirements: dict | None = None
    status: JobStatus
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
