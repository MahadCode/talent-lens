"""Repository for `RefreshToken` persistence operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.repositories.base import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Data-access operations for `RefreshToken` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=RefreshToken)

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        """Fetch a refresh token record by its JWT ID claim.

        Args:
            jti: The unique JWT ID to look up.

        Returns:
            The matching `RefreshToken`, or None if not found.
        """

        result = await self._session.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.scalar_one_or_none()

    async def revoke(self, refresh_token: RefreshToken) -> None:
        """Mark a refresh token as revoked.

        Args:
            refresh_token: The token record to revoke.
        """

        refresh_token.is_revoked = True
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: uuid.UUID) -> None:
        """Revoke every active refresh token belonging to a user.

        Used on password change or "log out of all devices".

        Args:
            user_id: The user whose tokens should be revoked.
        """

        await self._session.execute(
            update(RefreshToken).where(RefreshToken.user_id == user_id).values(is_revoked=True)
        )
        await self._session.flush()
