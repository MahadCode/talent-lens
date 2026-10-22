"""Repository for `Interview` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import Interview
from app.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[Interview]):
    """Data-access operations for `Interview` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=Interview)

    async def list_by_candidate(self, candidate_id: uuid.UUID) -> list[Interview]:
        """List all interview sessions for a given candidate.

        Args:
            candidate_id: The candidate to filter interviews by.

        Returns:
            A list of matching `Interview` instances.
        """

        result = await self._session.execute(
            select(Interview).where(Interview.candidate_id == candidate_id)
        )
        return list(result.scalars().all())

    async def get_question_bank(self, candidate_id: uuid.UUID) -> Interview | None:
        """Return the newest interview row that stores a question set.

        Args:
            candidate_id: The candidate whose question bank to load.

        Returns:
            The latest `Interview` with a non-null `questions` payload, or None.
        """

        query = (
            select(Interview)
            .where(Interview.candidate_id == candidate_id, Interview.questions.is_not(None))
            .order_by(Interview.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def find_by_question_id(self, question_id: str) -> Interview | None:
        """Find the interview whose question JSON contains this id.

        Args:
            question_id: The question id stored inside the JSON array.

        Returns:
            The matching `Interview`, or None.
        """

        query = select(Interview).where(Interview.questions.contains([{"id": question_id}]))
        result = await self._session.execute(query)
        return result.scalar_one_or_none()
