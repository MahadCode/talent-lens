"""Repository for `Score` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.score import Score
from app.repositories.base import BaseRepository


class ScoreRepository(BaseRepository[Score]):
    """Data-access operations for `Score` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=Score)

    async def get_latest_for_candidate(self, candidate_id: uuid.UUID) -> Score | None:
        """Fetch the most recently created score for a candidate.

        Args:
            candidate_id: The candidate to look up.

        Returns:
            The latest `Score`, or None if the candidate has never been scored.
        """

        query = (
            select(Score)
            .where(Score.candidate_id == candidate_id)
            .order_by(Score.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
