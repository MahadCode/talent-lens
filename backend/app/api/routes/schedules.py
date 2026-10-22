"""Scheduled interview endpoints. Distinct from the AI `/interview` routes."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.constants import INTERVIEW_ROLES
from app.core.dependencies import get_current_user, get_schedule_service, require_roles
from app.models.user import User
from app.schemas.schedule import InterviewDecisionRequest, InterviewFeedbackRequest, ScheduleCreate, ScheduleRead
from app.services.schedule_service import ScheduleService

router = APIRouter(
    prefix="/interviews",
    tags=["Scheduled interviews"],
    dependencies=[Depends(require_roles(*INTERVIEW_ROLES))],
)


@router.post(
    "",
    response_model=ScheduleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule an interview",
    description="Books an interview for a shortlisted candidate. Overlaps are saved and flagged.",
    responses={404: {"description": "Candidate not found."}, 422: {"description": "Candidate is not shortlisted."}},
)
async def schedule_interview(
    payload: ScheduleCreate,
    current_user: User = Depends(get_current_user),
    schedule_service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleRead:
    """Book an interview.

    Args:
        payload: Schedule details.
        current_user: The staff user booking the interview.
        schedule_service: Injected `ScheduleService`.

    Returns:
        The booked interview. `conflict` is true when the interviewer is busy.
    """

    return await schedule_service.schedule(payload, current_user.id)


@router.get(
    "",
    response_model=list[ScheduleRead],
    summary="List scheduled interviews",
)
async def list_scheduled_interviews(
    starts: datetime | None = Query(default=None, alias="from"),
    ends: datetime | None = Query(default=None, alias="to"),
    candidate_id: uuid.UUID | None = Query(default=None),
    schedule_service: ScheduleService = Depends(get_schedule_service),
) -> list[ScheduleRead]:
    """List booked interviews.

    Args:
        starts: Include interviews at or after this time.
        ends: Include interviews at or before this time.
        candidate_id: Optional candidate filter.
        schedule_service: Injected `ScheduleService`.

    Returns:
        Matching interviews, earliest first.
    """

    return await schedule_service.list_interviews(starts=starts, ends=ends, candidate_id=candidate_id)


@router.post(
    "/{interview_id}/feedback",
    response_model=ScheduleRead,
    summary="Store interviewer feedback",
    responses={404: {"description": "Interview not found."}},
)
async def save_feedback(
    interview_id: uuid.UUID,
    payload: InterviewFeedbackRequest,
    schedule_service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleRead:
    """Store structured feedback on a booked interview.

    Args:
        interview_id: The scheduled interview id.
        payload: Ratings and comments.
        schedule_service: Injected `ScheduleService`.

    Returns:
        The updated interview.
    """

    return await schedule_service.save_feedback(interview_id, payload)


@router.post(
    "/{interview_id}/decision",
    response_model=ScheduleRead,
    summary="Record a final hiring decision",
    responses={
        404: {"description": "Interview not found."},
        422: {"description": "Candidate is not in INTERVIEWING."},
    },
)
async def record_decision(
    interview_id: uuid.UUID,
    payload: InterviewDecisionRequest,
    current_user: User = Depends(get_current_user),
    schedule_service: ScheduleService = Depends(get_schedule_service),
) -> ScheduleRead:
    """Record HIRED or NOT_HIRED and update the candidate.

    Args:
        interview_id: The scheduled interview id.
        payload: The decision.
        current_user: The staff user recording the decision.
        schedule_service: Injected `ScheduleService`.

    Returns:
        The updated interview.
    """

    return await schedule_service.record_decision(interview_id, payload, current_user.id)
