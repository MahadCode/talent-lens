"""Business logic for user profile management and admin user operations."""

from __future__ import annotations

import uuid

from app.exceptions.errors import NotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import ProfileUpdate, UserUpdate


class UserService:
    """Coordinates reading, updating, and deleting `User` accounts."""

    def __init__(self, user_repo: UserRepository) -> None:
        """Initialize the service.

        Args:
            user_repo: Repository for `User` persistence.
        """

        self._user_repo = user_repo

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Fetch a user by id.

        Args:
            user_id: The user's id.

        Returns:
            The matching `User`.

        Raises:
            NotFoundError: If no user with this id exists.
        """

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise NotFoundError("User not found.")
        return user

    async def list_users(self, offset: int = 0, limit: int = 20) -> list[User]:
        """List users with pagination (ADMIN only, enforced at the route layer).

        Args:
            offset: Number of rows to skip.
            limit: Maximum number of rows to return.

        Returns:
            A list of `User` instances.
        """

        return await self._user_repo.list_all(offset=offset, limit=limit)

    async def update_user(self, user_id: uuid.UUID, update: UserUpdate) -> User:
        """Update an arbitrary user's account fields (ADMIN operation).

        Args:
            user_id: The id of the user to update.
            update: The fields to change; unset fields are left untouched.

        Returns:
            The updated `User`.

        Raises:
            NotFoundError: If no user with this id exists.
        """

        user = await self.get_by_id(user_id)
        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return user

    async def update_profile(self, user: User, update: ProfileUpdate) -> User:
        """Update the currently authenticated user's own profile.

        Args:
            user: The authenticated user.
            update: The fields to change; unset fields are left untouched.

        Returns:
            The updated `User`.
        """

        for field, value in update.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return user

    async def set_profile_image(self, user: User, image_path: str) -> User:
        """Set the stored profile image path/URL for a user.

        Args:
            user: The user whose profile image is being updated.
            image_path: The storage path or URL of the uploaded image.

        Returns:
            The updated `User`.
        """

        user.profile_image = image_path
        return user

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete a user account (ADMIN operation).

        Args:
            user_id: The id of the user to delete.

        Raises:
            NotFoundError: If no user with this id exists.
        """

        user = await self.get_by_id(user_id)
        await self._user_repo.delete(user)
