"""Tests for dashboard counts, shortlist rate, processing time, and skill gaps."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.constants import CandidateStatus, JobStatus
from app.exceptions.errors import NotFoundError
from app.models.candidate import Candidate
from app.models.candidate_status_event import CandidateStatusEvent
from app.models.job import Job
from app.models.scheduled_interview import ScheduledInterview
from app.core.constants import InterviewType
from app.services.analytics_service import AnalyticsService, build_job_analytics
import pytest


def _service():
    from tests.fakes import MemoryCandidateRepo, MemoryEventRepo, MemoryJobRepo, MemoryScheduleRepo

    jobs = MemoryJobRepo()
    candidates = MemoryCandidateRepo()
    schedules = MemoryScheduleRepo()
    events = MemoryEventRepo(candidates)
    service = AnalyticsService(
        job_repo=jobs, candidate_repo=candidates, schedule_repo=schedules, event_repo=events
    )
    return service, jobs, candidates, schedules, events


async def test_summary_counts_follow_live_rows() -> None:
    service, jobs, candidates, schedules, _ = _service()
    await jobs.add(
        Job(
            title="Open role",
            description="d",
            requirements="r",
            status=JobStatus.OPEN,
            created_by_id=uuid.uuid4(),
        )
    )
    await jobs.add(
        Job(
            title="Draft role",
            description="d",
            requirements="r",
            status=JobStatus.DRAFT,
            created_by_id=uuid.uuid4(),
        )
    )
    await candidates.add(Candidate(job_id=uuid.uuid4(), status=CandidateStatus.SHORTLISTED, score_overridden=False))
    await candidates.add(Candidate(job_id=uuid.uuid4(), status=CandidateStatus.MANUAL_REVIEW, score_overridden=False))
    now = datetime(2026, 11, 5, 12, 0, tzinfo=timezone.utc)
    await schedules.add(
        ScheduledInterview(
            candidate_id=uuid.uuid4(),
            scheduled_at=now + timedelta(hours=2),
            interviewer_name="Ada",
            interview_type=InterviewType.PHONE,
            created_by_id=uuid.uuid4(),
        )
    )
    await schedules.add(
        ScheduledInterview(
            candidate_id=uuid.uuid4(),
            scheduled_at=now - timedelta(hours=2),
            interviewer_name="Ada",
            interview_type=InterviewType.PHONE,
            created_by_id=uuid.uuid4(),
        )
    )

    summary = await service.summary(now=now)

    assert summary.active_jobs == 1
    assert summary.applications == 2
    assert summary.shortlisted == 1
    assert summary.pending_reviews == 1
    assert summary.upcoming_interviews == 1


async def test_job_report_rate_time_and_gaps() -> None:
    service, jobs, candidates, _, events = _service()
    job = await jobs.add(
        Job(
            title="Backend Developer",
            description="d",
            requirements="r",
            status=JobStatus.OPEN,
            created_by_id=uuid.uuid4(),
        )
    )
    created = datetime(2026, 11, 1, 9, 0, tzinfo=timezone.utc)
    shortlisted = Candidate(
        job_id=job.id,
        status=CandidateStatus.SHORTLISTED,
        score_overridden=False,
        matching_result={"missing_skills": ["Docker", "Kubernetes"]},
    )
    hired = Candidate(
        job_id=job.id,
        status=CandidateStatus.HIRED,
        score_overridden=False,
        matching_result={"missing_skills": ["Docker"]},
    )
    rejected = Candidate(job_id=job.id, status=CandidateStatus.REJECTED, score_overridden=False, matching_result=None)
    interviewing = Candidate(job_id=job.id, status=CandidateStatus.INTERVIEWING, score_overridden=False)
    for candidate in (shortlisted, hired, rejected, interviewing):
        candidate.created_at = created
        await candidates.add(candidate)

    await events.add(
        CandidateStatusEvent(
            candidate_id=shortlisted.id,
            actor_id=uuid.uuid4(),
            from_status=CandidateStatus.PARSED,
            to_status=CandidateStatus.SHORTLISTED,
        )
    )
    events.rows[-1].created_at = created + timedelta(hours=2)

    report = await service.job_report(job.id)

    assert report.application_to_shortlist_rate == 0.75
    assert report.average_processing_hours == 2.0
    assert report.common_skill_gaps[0].skill == "Docker"
    assert report.common_skill_gaps[0].count == 2
    assert report.counts_by_status["REJECTED"] == 1


async def test_missing_job_report_raises() -> None:
    service, _, _, _, _ = _service()
    with pytest.raises(NotFoundError):
        await service.job_report(uuid.uuid4())


def test_empty_job_has_a_zero_rate() -> None:
    report = build_job_analytics(uuid.uuid4(), {}, [], [])
    assert report.application_to_shortlist_rate == 0.0
    assert report.average_processing_hours is None
