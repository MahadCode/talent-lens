"""Repository for human-scheduled interviews."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scheduled_interview import ScheduledInterview
from app.repositories.base import BaseRepository

CONFLICT_WINDOW = timedelta(minutes=60)


class ScheduledInterviewRepository(BaseRepository[ScheduledInterview]):
    """Data-access operations for `ScheduledInterview` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=ScheduledInterview)

    async def list_filtered(
        self,
        starts: datetime | None = None,
        ends: datetime | None = None,
        candidate_id: uuid.UUID | None = None,
    ) -> list[ScheduledInterview]:
        """List scheduled interviews, optionally filtered by time and candidate.

        Args:
            starts: Include interviews at or after this time.
            ends: Include interviews at or before this time.
            candidate_id: If set, only this candidate's interviews.

        Returns:
            Matching interviews ordered by start time.
        """

        query = select(ScheduledInterview).order_by(ScheduledInterview.scheduled_at.asc())
        if starts is not None:
            query = query.where(ScheduledInterview.scheduled_at >= starts)
        if ends is not None:
            query = query.where(ScheduledInterview.scheduled_at <= ends)
        if candidate_id is not None:
            query = query.where(ScheduledInterview.candidate_id == candidate_id)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def find_conflict(
        self, interviewer_name: str, scheduled_at: datetime
    ) -> ScheduledInterview | None:
        """Find an interview for the same interviewer within 60 minutes.

        Args:
            interviewer_name: Already trimmed, case-folded interviewer name.
            scheduled_at: Proposed start time.

        Returns:
            The first conflicting interview, or None.
        """

        start = scheduled_at - CONFLICT_WINDOW
        end = scheduled_at + CONFLICT_WINDOW
        query = (
            select(ScheduledInterview)
            .where(
                func.lower(func.trim(ScheduledInterview.interviewer_name)) == interviewer_name,
                ScheduledInterview.scheduled_at >= start,
                ScheduledInterview.scheduled_at <= end,
            )
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def count_upcoming(self, now: datetime) -> int:
        """Count interviews scheduled strictly after `now`.

        Args:
            now: The current time.

        Returns:
            The number of upcoming interviews.
        """

        query = (
            select(func.count())
            .select_from(ScheduledInterview)
            .where(ScheduledInterview.scheduled_at > now)
        )
        result = await self._session.execute(query)
        return int(result.scalar_one())
