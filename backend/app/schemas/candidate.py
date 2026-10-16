"""Pydantic schemas for candidate resources."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import CandidateStatus


class CandidateRead(BaseModel):
    """Public representation of a candidate."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    job_id: uuid.UUID
    full_name: str | None = None
    email: str | None = None
    github_url: str | None = None
    status: CandidateStatus
    parsed_profile: dict[str, Any] | None = None
    match_percentage: float | None = None
    score_overridden: bool = False
    created_at: datetime
    updated_at: datetime


class AssessmentRead(BaseModel):
    """Stored score plus the matcher explanation for one candidate."""

    candidate_id: uuid.UUID
    total_score: float
    skills_score: float
    experience_score: float
    projects_score: float
    education_score: float
    certifications_score: float
    reasoning: str
    match_percentage: float | None = None
    missing_skills: list[str] = Field(default_factory=list)
    extra_skills: list[str] = Field(default_factory=list)
    experience_comparison: str | None = None
    explanation: str | None = None
    score_overridden: bool = False


class CandidateStatusUpdate(BaseModel):
    """Request body for `PATCH /candidates/{id}/status`."""

    status: CandidateStatus


class CandidateNoteCreate(BaseModel):
    """Request body for `POST /candidates/{id}/notes`."""

    body: str = Field(..., min_length=1)


class CandidateNoteRead(BaseModel):
    """A private recruiter note. Not included on `CandidateRead`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    created_at: datetime


class CandidateStatusEventRead(BaseModel):
    """One recorded pipeline status change."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    actor_id: uuid.UUID
    from_status: CandidateStatus
    to_status: CandidateStatus
    created_at: datetime


class CandidateProfileUpdate(BaseModel):
    """Fields a recruiter may correct on a parsed resume."""

    skills: list[str] | None = None
    experience: list[str] | None = None
    projects: list[str] | None = None
    education: list[str] | None = None
    certifications: list[str] | None = None


class ScoreOverrideRequest(BaseModel):
    """Request body for `PATCH /candidates/{id}/score`."""

    total_score: float = Field(..., ge=0, le=100)
    reason: str = Field(..., min_length=1)


class CandidateApplicationRead(BaseModel):
    """A candidate's own application. Recruiter-only fields are omitted."""

    id: uuid.UUID
    job_id: uuid.UUID
    job_title: str | None = None
    status: CandidateStatus
    parsed_profile: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
