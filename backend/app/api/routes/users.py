"""User management endpoints. All routes here are restricted to ADMIN users."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_user_service, require_admin
from app.schemas.common import MessageResponse
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"], dependencies=[Depends(require_admin())])


@router.get(
    "",
    response_model=list[UserRead],
    summary="List users",
    description="Lists all registered users. ADMIN only.",
)
async def list_users(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_service: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """List all users with pagination.

    Args:
        offset: Number of rows to skip.
        limit: Maximum number of rows to return.
        user_service: Injected `UserService`.

    Returns:
        A list of user profiles.
    """

    users = await user_service.list_users(offset=offset, limit=limit)
    return [UserRead.model_validate(user) for user in users]


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get a user by id",
    description="Fetches a single user's profile by id. ADMIN only.",
    responses={404: {"description": "User not found."}},
)
async def get_user(user_id: uuid.UUID, user_service: UserService = Depends(get_user_service)) -> UserRead:
    """Fetch a single user by id.

    Args:
        user_id: The user's id.
        user_service: Injected `UserService`.

    Returns:
        The matching user's profile.
    """

    user = await user_service.get_by_id(user_id)
    return UserRead.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Update a user",
    description="Updates another user's account fields (role, active status, etc). ADMIN only.",
    responses={404: {"description": "User not found."}},
)
async def update_user(
    user_id: uuid.UUID, payload: UserUpdate, user_service: UserService = Depends(get_user_service)
) -> UserRead:
    """Update a user's account.

    Args:
        user_id: The id of the user to update.
        payload: Fields to update.
        user_service: Injected `UserService`.

    Returns:
        The updated user's profile.
    """

    updated = await user_service.update_user(user_id, payload)
    return UserRead.model_validate(updated)


@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete a user",
    description="Permanently deletes a user account. ADMIN only.",
    responses={404: {"description": "User not found."}},
)
async def delete_user(
    user_id: uuid.UUID, user_service: UserService = Depends(get_user_service)
) -> MessageResponse:
    """Delete a user account.

    Args:
        user_id: The id of the user to delete.
        user_service: Injected `UserService`.

    Returns:
        A confirmation message.
    """

    await user_service.delete_user(user_id)
    return MessageResponse(message="User deleted successfully.")
