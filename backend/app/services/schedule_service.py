"""Business logic for booking interviews and recording human decisions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.constants import CandidateStatus, HiringDecision
from app.exceptions.errors import NotFoundError, ValidationAppError
from app.models.candidate_status_event import CandidateStatusEvent
from app.models.scheduled_interview import ScheduledInterview
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_status_event_repository import CandidateStatusEventRepository
from app.repositories.scheduled_interview_repository import ScheduledInterviewRepository
from app.schemas.schedule import (
    InterviewDecisionRequest,
    InterviewFeedbackRequest,
    ScheduleCreate,
    ScheduleRead,
)
from app.services.pipeline_rules import assert_transition


class ScheduleService:
    """Books interviews and stores interviewer feedback and final decisions."""

    def __init__(
        self,
        candidate_repo: CandidateRepository,
        schedule_repo: ScheduledInterviewRepository,
        event_repo: CandidateStatusEventRepository,
    ) -> None:
        """Initialize the service.

        Args:
            candidate_repo: Repository for `Candidate` persistence.
            schedule_repo: Repository for `ScheduledInterview` persistence.
            event_repo: Repository for status audit events.
        """

        self._candidate_repo = candidate_repo
        self._schedule_repo = schedule_repo
        self._event_repo = event_repo

    async def schedule(self, data: ScheduleCreate, actor_id: uuid.UUID) -> ScheduleRead:
        """Book an interview and move a shortlisted candidate to INTERVIEWING.

        A booking that overlaps the same interviewer by 60 minutes is still
        saved. The response flags the conflict instead of rejecting it.

        Args:
            data: Schedule details.
            actor_id: The staff user booking the interview.

        Returns:
            The saved interview, including a conflict flag.

        Raises:
            NotFoundError: If the candidate does not exist.
            ValidationAppError: If the time has no timezone, or the candidate
                is not shortlisted or already interviewing.
        """

        if data.scheduled_at.tzinfo is None:
            raise ValidationAppError("scheduled_at must include a timezone.")

        candidate = await self._candidate_repo.get_by_id(data.candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")

        if candidate.status == CandidateStatus.SHORTLISTED:
            assert_transition(candidate.status, CandidateStatus.INTERVIEWING)
            candidate.status = CandidateStatus.INTERVIEWING
            await self._event_repo.add(
                CandidateStatusEvent(
                    candidate_id=candidate.id,
                    actor_id=actor_id,
                    from_status=CandidateStatus.SHORTLISTED,
                    to_status=CandidateStatus.INTERVIEWING,
                )
            )
        elif candidate.status != CandidateStatus.INTERVIEWING:
            raise ValidationAppError(
                f"Cannot schedule an interview while the candidate is {candidate.status.value}."
            )

        normalized_name = data.interviewer_name.strip().casefold()
        conflict = await self._schedule_repo.find_conflict(normalized_name, data.scheduled_at)
        interview = await self._schedule_repo.add(
            ScheduledInterview(
                candidate_id=candidate.id,
                scheduled_at=data.scheduled_at,
                interviewer_name=data.interviewer_name.strip(),
                interview_type=data.interview_type,
                notes=data.notes,
                created_by_id=actor_id,
            )
        )
        return _to_read(
            interview,
            conflict=conflict is not None,
            conflicting_interview_id=None if conflict is None else conflict.id,
        )

    async def list_interviews(
        self,
        starts: datetime | None = None,
        ends: datetime | None = None,
        candidate_id: uuid.UUID | None = None,
    ) -> list[ScheduleRead]:
        """List booked interviews.

        Args:
            starts: Include interviews at or after this time.
            ends: Include interviews at or before this time.
            candidate_id: If set, only this candidate's interviews.

        Returns:
            Interview records. Conflict flags are false on this read path.
        """

        rows = await self._schedule_repo.list_filtered(starts=starts, ends=ends, candidate_id=candidate_id)
        return [_to_read(row, conflict=False, conflicting_interview_id=None) for row in rows]

    async def save_feedback(self, interview_id: uuid.UUID, data: InterviewFeedbackRequest) -> ScheduleRead:
        """Store structured interviewer feedback.

        Args:
            interview_id: The scheduled interview to update.
            data: Ratings and comments.

        Returns:
            The updated interview.

        Raises:
            NotFoundError: If the interview does not exist.
        """

        interview = await self._get_interview(interview_id)
        interview.feedback = {"ratings": data.ratings, "comments": data.comments}
        return _to_read(interview, conflict=False, conflicting_interview_id=None)

    async def record_decision(
        self, interview_id: uuid.UUID, data: InterviewDecisionRequest, actor_id: uuid.UUID
    ) -> ScheduleRead:
        """Record a final hire decision and move the candidate.

        Args:
            interview_id: The scheduled interview the decision belongs to.
            data: HIRED or NOT_HIRED.
            actor_id: The staff user recording the decision.

        Returns:
            The updated interview.

        Raises:
            NotFoundError: If the interview or candidate does not exist.
            ValidationAppError: If the candidate is not in INTERVIEWING.
        """

        interview = await self._get_interview(interview_id)
        candidate = await self._candidate_repo.get_by_id(interview.candidate_id)
        if candidate is None:
            raise NotFoundError("Candidate not found.")

        target = CandidateStatus(data.decision.value)
        assert_transition(candidate.status, target)
        previous = candidate.status
        candidate.status = target
        interview.decision = HiringDecision(data.decision.value)
        await self._event_repo.add(
            CandidateStatusEvent(
                candidate_id=candidate.id,
                actor_id=actor_id,
                from_status=previous,
                to_status=target,
            )
        )
        return _to_read(interview, conflict=False, conflicting_interview_id=None)

    async def _get_interview(self, interview_id: uuid.UUID) -> ScheduledInterview:
        """Load one scheduled interview or raise not found.

        Args:
            interview_id: The interview id.

        Returns:
            The matching row.

        Raises:
            NotFoundError: If the interview does not exist.
        """

        interview = await self._schedule_repo.get_by_id(interview_id)
        if interview is None:
            raise NotFoundError("Interview not found.")
        return interview


def _to_read(
    interview: ScheduledInterview, conflict: bool, conflicting_interview_id: uuid.UUID | None
) -> ScheduleRead:
    """Build the API representation of a scheduled interview.

    Args:
        interview: The stored interview.
        conflict: Whether the booking overlaps another interview.
        conflicting_interview_id: The other interview, when there is a conflict.

    Returns:
        A `ScheduleRead` payload.
    """

    return ScheduleRead(
        id=interview.id,
        candidate_id=interview.candidate_id,
        scheduled_at=interview.scheduled_at,
        interviewer_name=interview.interviewer_name,
        interview_type=interview.interview_type,
        notes=interview.notes,
        feedback=interview.feedback,
        decision=interview.decision,
        conflict=conflict,
        conflicting_interview_id=conflicting_interview_id,
        created_at=interview.created_at or datetime.now(timezone.utc),
    )
