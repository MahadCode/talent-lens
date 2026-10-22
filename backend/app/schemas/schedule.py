"""Pydantic schemas for scheduled interviews."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import HiringDecision, InterviewType


class ScheduleCreate(BaseModel):
    """Request body for `POST /interviews`."""

    candidate_id: uuid.UUID
    scheduled_at: datetime
    interviewer_name: str = Field(..., min_length=1, max_length=255)
    interview_type: InterviewType
    notes: str | None = None


class ScheduleRead(BaseModel):
    """A booked interview, including a soft scheduling-conflict flag."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    candidate_id: uuid.UUID
    scheduled_at: datetime
    interviewer_name: str
    interview_type: InterviewType
    notes: str | None = None
    feedback: dict | None = None
    decision: HiringDecision | None = None
    conflict: bool = False
    conflicting_interview_id: uuid.UUID | None = None
    created_at: datetime


class InterviewFeedbackRequest(BaseModel):
    """Request body for `POST /interviews/{id}/feedback`."""

    ratings: dict[str, int] = Field(default_factory=dict)
    comments: str = ""


class InterviewDecisionRequest(BaseModel):
    """Request body for `POST /interviews/{id}/decision`."""

    decision: HiringDecision
