"""Repository for `User` persistence operations."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Data-access operations for `User` rows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The request-scoped async DB session.
        """

        super().__init__(session=session, model=User)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by their unique email address.

        Args:
            email: The email address to look up.

        Returns:
            The matching `User`, or None if not found.
        """

        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
