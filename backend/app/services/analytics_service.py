"""Recruiting dashboard counts computed from live pipeline data."""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timezone

from app.core.constants import CandidateStatus, JobStatus
from app.exceptions.errors import NotFoundError
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.candidate_status_event_repository import CandidateStatusEventRepository
from app.repositories.job_repository import JobRepository
from app.repositories.scheduled_interview_repository import ScheduledInterviewRepository
from app.schemas.analytics import AnalyticsSummary, JobAnalytics, SkillGapCount

_SHORTLIST_STATUSES = (
    CandidateStatus.SHORTLISTED,
    CandidateStatus.INTERVIEWING,
    CandidateStatus.HIRED,
)


class AnalyticsService:
    """Reads pipeline tables and returns dashboard figures."""

    def __init__(
        self,
        job_repo: JobRepository,
        candidate_repo: CandidateRepository,
        schedule_repo: ScheduledInterviewRepository,
        event_repo: CandidateStatusEventRepository,
    ) -> None:
        """Initialize the service.

        Args:
            job_repo: Repository for `Job` persistence.
            candidate_repo: Repository for `Candidate` persistence.
            schedule_repo: Repository for scheduled interviews.
            event_repo: Repository for status audit events.
        """

        self._job_repo = job_repo
        self._candidate_repo = candidate_repo
        self._schedule_repo = schedule_repo
        self._event_repo = event_repo

    async def summary(self, now: datetime | None = None) -> AnalyticsSummary:
        """Return the recruiter dashboard counts.

        Args:
            now: Clock injection for tests. Defaults to the current UTC time.

        Returns:
            Active jobs, applications, shortlisted candidates, pending reviews,
            and upcoming interviews.
        """

        clock = now or datetime.now(timezone.utc)
        return AnalyticsSummary(
            active_jobs=await self._job_repo.count_by_status(JobStatus.OPEN),
            applications=await self._candidate_repo.count(),
            shortlisted=await self._candidate_repo.count(status=CandidateStatus.SHORTLISTED),
            pending_reviews=await self._candidate_repo.count(status=CandidateStatus.MANUAL_REVIEW),
            upcoming_interviews=await self._schedule_repo.count_upcoming(clock),
        )

    async def job_report(self, job_id: uuid.UUID) -> JobAnalytics:
        """Return stage, rate, timing, and skill-gap figures for one job.

        Args:
            job_id: The job to report on.

        Returns:
            The job analytics payload.

        Raises:
            NotFoundError: If the job does not exist.
        """

        job = await self._job_repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("Job not found.")

        counts = await self._candidate_repo.status_counts_for_job(job_id)
        samples = await self._event_repo.processing_samples(job_id)
        matching_results = await self._candidate_repo.list_matching_results(job_id)
        return build_job_analytics(job_id, counts, samples, matching_results)


def build_job_analytics(
    job_id: uuid.UUID,
    status_counts: dict[str, int],
    samples: list[tuple[datetime, datetime | None]],
    matching_results: list[dict | None],
) -> JobAnalytics:
    """Assemble one job's analytics from already-loaded rows.

    Shortlist rate is `(SHORTLISTED + INTERVIEWING + HIRED) / applications`.
    Average processing time is the mean hours from candidate creation to the
    first status event whose previous status was `PARSED`.

    Args:
        job_id: The job these rows belong to.
        status_counts: Status value to count. Missing statuses are treated as zero.
        samples: `(created_at, first_exit_from_parsed)` pairs.
        matching_results: Stored matcher payloads. None entries are ignored.

    Returns:
        A `JobAnalytics` payload.
    """

    counts = {status.value: int(status_counts.get(status.value, 0)) for status in CandidateStatus}
    total = sum(counts.values())
    shortlisted_like = sum(counts[status.value] for status in _SHORTLIST_STATUSES)
    rate = (shortlisted_like / total) if total else 0.0

    hours: list[float] = []
    for created_at, left_parsed_at in samples:
        if left_parsed_at is None:
            continue
        delta = left_parsed_at - created_at
        hours.append(delta.total_seconds() / 3600)

    average = round(sum(hours) / len(hours), 2) if hours else None
    gaps = Counter()
    for result in matching_results:
        if not result:
            continue
        for skill in result.get("missing_skills") or []:
            if isinstance(skill, str) and skill.strip():
                gaps[skill.strip()] += 1

    common = [
        SkillGapCount(skill=skill, count=count)
        for skill, count in sorted(gaps.items(), key=lambda item: (-item[1], item[0]))[:10]
    ]
    return JobAnalytics(
        job_id=job_id,
        counts_by_status=counts,
        application_to_shortlist_rate=round(rate, 4),
        average_processing_hours=average,
        common_skill_gaps=common,
    )
