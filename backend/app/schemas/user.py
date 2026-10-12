"""Pydantic schemas for user resources."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.constants import UserRole


class UserRead(BaseModel):
    """Public representation of a user, safe to return from the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: EmailStr
    role: UserRole
    company_name: str | None = None
    profile_image: str | None = None
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool = False
    created_at: datetime
    last_login: datetime | None = None


class UserUpdate(BaseModel):
    """Fields an ADMIN may update on another user's account."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    company_name: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class ProfileUpdate(BaseModel):
    """Fields a user may update on their own profile."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)


class ProfileImageResponse(BaseModel):
    """Response returned after a successful profile image upload."""

    profile_image: str = Field(..., description="URL or storage path of the uploaded image.")
