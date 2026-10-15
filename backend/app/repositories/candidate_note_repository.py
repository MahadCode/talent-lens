"""Repository for `CandidateNote` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.candidate_note import CandidateNote
from app.repositories.base import BaseRepository


class CandidateNoteRepository(BaseRepository[CandidateNote]):
    """Data-access operations for private recruiter notes."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=CandidateNote)

    async def list_for_candidate(self, candidate_id: uuid.UUID) -> list[CandidateNote]:
        """List notes for a candidate, newest first.

        Args:
            candidate_id: The candidate whose notes to load.

        Returns:
            Notes ordered by `created_at` descending.
        """

        result = await self._session.execute(
            select(CandidateNote)
            .where(CandidateNote.candidate_id == candidate_id)
            .order_by(CandidateNote.created_at.desc())
        )
        return list(result.scalars().all())
