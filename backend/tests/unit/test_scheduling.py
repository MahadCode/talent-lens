"""Tests for interview booking, conflict warnings, feedback, and final decisions."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.constants import CandidateStatus, HiringDecision, InterviewType
from app.exceptions.errors import ValidationAppError
from app.models.candidate import Candidate
from app.schemas.schedule import InterviewDecisionRequest, InterviewFeedbackRequest, ScheduleCreate
from app.services.schedule_service import ScheduleService
from tests.fakes import MemoryCandidateRepo, MemoryEventRepo, MemoryScheduleRepo


def _service():
    candidates = MemoryCandidateRepo()
    schedules = MemoryScheduleRepo()
    events = MemoryEventRepo(candidates)
    service = ScheduleService(candidate_repo=candidates, schedule_repo=schedules, event_repo=events)
    return service, candidates, schedules


async def _shortlisted() -> tuple[ScheduleService, Candidate]:
    service, candidates, _ = _service()
    candidate = Candidate(job_id=uuid.uuid4(), status=CandidateStatus.SHORTLISTED, score_overridden=False)
    await candidates.add(candidate)
    return service, candidate


def _booking(candidate_id: uuid.UUID, when: datetime, name: str = "Ada Lovelace") -> ScheduleCreate:
    return ScheduleCreate(
        candidate_id=candidate_id,
        scheduled_at=when,
        interviewer_name=name,
        interview_type=InterviewType.VIDEO,
    )


async def test_scheduling_shortlisted_candidate_moves_them_to_interviewing() -> None:
    service, candidate = await _shortlisted()
    when = datetime(2026, 11, 6, 15, 0, tzinfo=timezone.utc)

    booked = await service.schedule(_booking(candidate.id, when), uuid.uuid4())

    assert booked.conflict is False
    assert candidate.status == CandidateStatus.INTERVIEWING
    history = await service._event_repo.list_for_candidate(candidate.id)
    assert history[0].to_status == CandidateStatus.INTERVIEWING


async def test_overlap_is_flagged_and_still_saved() -> None:
    service, candidate = await _shortlisted()
    start = datetime(2026, 11, 6, 15, 0, tzinfo=timezone.utc)
    actor = uuid.uuid4()
    await service.schedule(_booking(candidate.id, start, "Ada Lovelace"), actor)

    overlap = await service.schedule(
        _booking(candidate.id, start + timedelta(minutes=60), " ada lovelace "), actor
    )
    clear = await service.schedule(
        _booking(candidate.id, start + timedelta(minutes=121), "Ada Lovelace"), actor
    )

    assert overlap.conflict is True
    assert overlap.conflicting_interview_id is not None
    assert clear.conflict is False
    listed = await service.list_interviews(candidate_id=candidate.id)
    assert len(listed) == 3


async def test_naive_time_and_unshortlisted_candidate_are_rejected() -> None:
    service, candidate = await _shortlisted()
    candidate.status = CandidateStatus.PARSED

    with pytest.raises(ValidationAppError):
        await service.schedule(
            _booking(candidate.id, datetime(2026, 11, 6, 15, 0, tzinfo=timezone.utc)), uuid.uuid4()
        )

    candidate.status = CandidateStatus.SHORTLISTED
    with pytest.raises(ValidationAppError):
        await service.schedule(
            _booking(candidate.id, datetime(2026, 11, 6, 15, 0)), uuid.uuid4()
        )


async def test_feedback_and_decision_update_the_candidate() -> None:
    service, candidate = await _shortlisted()
    booked = await service.schedule(
        _booking(candidate.id, datetime(2026, 11, 6, 15, 0, tzinfo=timezone.utc)), uuid.uuid4()
    )

    with_feedback = await service.save_feedback(
        booked.id, InterviewFeedbackRequest(ratings={"communication": 4}, comments="Clear answers.")
    )
    decided = await service.record_decision(
        booked.id, InterviewDecisionRequest(decision=HiringDecision.HIRED), uuid.uuid4()
    )

    assert with_feedback.feedback["comments"] == "Clear answers."
    assert decided.decision == HiringDecision.HIRED
    assert candidate.status == CandidateStatus.HIRED
