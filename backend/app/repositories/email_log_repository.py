"""Repository for `EmailLog` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_log import EmailLog
from app.repositories.base import BaseRepository


class EmailLogRepository(BaseRepository[EmailLog]):
    """Data-access operations for `EmailLog` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=EmailLog)

    async def list_by_candidate(self, candidate_id: uuid.UUID) -> list[EmailLog]:
        """List all drafted emails for a given candidate.

        Args:
            candidate_id: The candidate to filter email logs by.

        Returns:
            A list of matching `EmailLog` instances.
        """

        result = await self._session.execute(select(EmailLog).where(EmailLog.candidate_id == candidate_id))
        return list(result.scalars().all())
