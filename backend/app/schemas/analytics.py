"""Pydantic schemas for recruitment analytics."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class AnalyticsSummary(BaseModel):
    """Recruiter dashboard counts."""

    active_jobs: int
    applications: int
    shortlisted: int
    pending_reviews: int
    upcoming_interviews: int


class SkillGapCount(BaseModel):
    """How often a required skill was missing across applicants for one job."""

    skill: str
    count: int


class JobAnalytics(BaseModel):
    """Stage, rate, timing, and skill-gap figures for one job."""

    job_id: uuid.UUID
    counts_by_status: dict[str, int]
    application_to_shortlist_rate: float
    average_processing_hours: float | None = None
    common_skill_gaps: list[SkillGapCount] = Field(default_factory=list)
