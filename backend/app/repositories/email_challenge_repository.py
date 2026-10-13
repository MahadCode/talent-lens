"""Persistence for hashed email OTP / magic-link challenges."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_challenge import EmailChallenge
from app.repositories.base import BaseRepository


class EmailChallengeRepository(BaseRepository[EmailChallenge]):
    """Data-access operations for `EmailChallenge` rows."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=EmailChallenge)

    async def get_active_by_id(self, challenge_id: uuid.UUID) -> EmailChallenge | None:
        result = await self._session.execute(
            select(EmailChallenge).where(
                EmailChallenge.id == challenge_id,
                EmailChallenge.consumed_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_by_link_hash(self, token_hash: str) -> EmailChallenge | None:
        result = await self._session.execute(
            select(EmailChallenge).where(
                EmailChallenge.link_token_hash == token_hash,
                EmailChallenge.consumed_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_for_user(self, user_id: uuid.UUID, purpose: str) -> EmailChallenge | None:
        result = await self._session.execute(
            select(EmailChallenge)
            .where(
                EmailChallenge.user_id == user_id,
                EmailChallenge.purpose == purpose,
                EmailChallenge.consumed_at.is_(None),
            )
            .order_by(EmailChallenge.created_at.desc())
        )
        return result.scalars().first()

    async def consume_open_for_user(self, user_id: uuid.UUID, purpose: str) -> None:
        now = datetime.now(timezone.utc)
        await self._session.execute(
            update(EmailChallenge)
            .where(
                EmailChallenge.user_id == user_id,
                EmailChallenge.purpose == purpose,
                EmailChallenge.consumed_at.is_(None),
            )
            .values(consumed_at=now)
        )
        await self._session.flush()

    async def count_recent(self, user_id: uuid.UUID, purpose: str, window: timedelta) -> int:
        cutoff = datetime.now(timezone.utc) - window
        result = await self._session.execute(
            select(EmailChallenge.id).where(
                EmailChallenge.user_id == user_id,
                EmailChallenge.purpose == purpose,
                EmailChallenge.created_at >= cutoff,
            )
        )
        return len(result.all())
