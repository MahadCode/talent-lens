"""Repository for candidate status audit events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CandidateStatus
from app.models.candidate import Candidate
from app.models.candidate_status_event import CandidateStatusEvent
from app.repositories.base import BaseRepository


class CandidateStatusEventRepository(BaseRepository[CandidateStatusEvent]):
    """Data-access operations for pipeline audit rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=CandidateStatusEvent)

    async def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateStatusEvent]:
        """List status changes for a candidate, oldest first.

        Args:
            candidate_id: The candidate whose history to load.

        Returns:
            Events ordered by `created_at` ascending.
        """

        result = await self._session.execute(
            select(CandidateStatusEvent)
            .where(CandidateStatusEvent.candidate_id == candidate_id)
            .order_by(CandidateStatusEvent.created_at.asc())
        )
        return list(result.scalars().all())

    async def processing_samples(self, job_id: uuid.UUID) -> list[tuple[datetime, datetime | None]]:
        """Return each candidate's created time and first exit from PARSED.

        Args:
            job_id: The job whose candidates to measure.

        Returns:
            Pairs of `(created_at, first_leave_parsed_at)`. The second value
            is None when the candidate has never left `PARSED`.
        """

        query = (
            select(Candidate.created_at, func.min(CandidateStatusEvent.created_at))
            .outerjoin(
                CandidateStatusEvent,
                and_(
                    CandidateStatusEvent.candidate_id == Candidate.id,
                    CandidateStatusEvent.from_status == CandidateStatus.PARSED,
                ),
            )
            .where(Candidate.job_id == job_id)
            .group_by(Candidate.id, Candidate.created_at)
        )
        rows = (await self._session.execute(query)).all()
        return [(row[0], row[1]) for row in rows]
