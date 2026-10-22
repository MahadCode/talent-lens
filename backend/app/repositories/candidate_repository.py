"""Repository for `Candidate` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CandidateStatus
from app.models.candidate import Candidate
from app.repositories.base import BaseRepository


class CandidateRepository(BaseRepository[Candidate]):
    """Data-access operations for `Candidate` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=Candidate)

    async def list_by_job(self, job_id: uuid.UUID, offset: int = 0, limit: int = 100) -> list[Candidate]:
        """List candidates evaluated against a specific job.

        Args:
            job_id: The job to filter candidates by.
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A list of matching `Candidate` instances.
        """

        query = select(Candidate).where(Candidate.job_id == job_id).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self, status: CandidateStatus | None = None, job_id: uuid.UUID | None = None
    ) -> int:
        """Count candidates, optionally filtered by status and job.

        Args:
            status: If provided, only candidates in this status are counted.
            job_id: If provided, only candidates for this job are counted.

        Returns:
            The matching row count.
        """

        query = select(func.count()).select_from(Candidate)
        if status is not None:
            query = query.where(Candidate.status == status)
        if job_id is not None:
            query = query.where(Candidate.job_id == job_id)
        result = await self._session.execute(query)
        return int(result.scalar_one())

    async def status_counts_for_job(self, job_id: uuid.UUID) -> dict[str, int]:
        """Count candidates on a job grouped by status.

        Args:
            job_id: The job to aggregate.

        Returns:
            A map of status value to count. Statuses with no rows are omitted.
        """

        query = (
            select(Candidate.status, func.count())
            .where(Candidate.job_id == job_id)
            .group_by(Candidate.status)
        )
        rows = (await self._session.execute(query)).all()
        return {status.value if isinstance(status, CandidateStatus) else str(status): int(count) for status, count in rows}

    async def list_matching_results(self, job_id: uuid.UUID) -> list[dict | None]:
        """Load stored matcher payloads for every candidate on a job.

        Args:
            job_id: The job to read.

        Returns:
            One entry per candidate. Missing results are None.
        """

        result = await self._session.execute(
            select(Candidate.matching_result).where(Candidate.job_id == job_id)
        )
        return list(result.scalars().all())

    async def get_by_user_and_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> Candidate | None:
        """Fetch the application a user already submitted for a job.

        Args:
            user_id: The candidate account.
            job_id: The job they applied to.

        Returns:
            The matching `Candidate`, or None.
        """

        query = select(Candidate).where(Candidate.user_id == user_id, Candidate.job_id == job_id)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: uuid.UUID) -> list[Candidate]:
        """List applications owned by a candidate account, newest first.

        Args:
            user_id: The candidate account.

        Returns:
            The user's applications.
        """

        query = (
            select(Candidate)
            .where(Candidate.user_id == user_id)
            .order_by(Candidate.created_at.desc())
        )
        result = await self._session.execute(query)
        return list(result.scalars().all())
