"""Repository for `Resume` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume
from app.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[Resume]):
    """Data-access operations for `Resume` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=Resume)

    async def list_by_candidate(self, candidate_id: uuid.UUID) -> list[Resume]:
        """List all resumes uploaded for a given candidate.

        Args:
            candidate_id: The candidate to filter resumes by.

        Returns:
            A list of matching `Resume` instances.
        """

        result = await self._session.execute(select(Resume).where(Resume.candidate_id == candidate_id))
        return list(result.scalars().all())

    async def get_latest_for_candidate(self, candidate_id: uuid.UUID) -> Resume | None:
        """Fetch the most recently uploaded resume for a candidate.

        Args:
            candidate_id: The candidate to look up.

        Returns:
            The latest `Resume`, or None if none have been uploaded.
        """

        query = (
            select(Resume)
            .where(Resume.candidate_id == candidate_id)
            .order_by(Resume.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
