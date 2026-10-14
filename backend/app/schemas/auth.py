"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.core.constants import UserRole
from app.schemas.user import UserRead


class RegisterRequest(BaseModel):
    """Request body for `POST /auth/register`."""

    full_name: str = Field(..., min_length=1, max_length=255, examples=["Jane Doe"])
    email: EmailStr = Field(..., examples=["jane.doe@example.com"])
    password: str = Field(..., min_length=8, max_length=128, examples=["StrongP@ssw0rd"])
    role: UserRole = Field(default=UserRole.RECRUITER)
    company_name: str | None = Field(default=None, max_length=255, examples=["Acme Corp"])


class LoginRequest(BaseModel):
    """Request body for `POST /auth/login`."""

    email: EmailStr = Field(..., examples=["jane.doe@example.com"])
    password: str = Field(..., min_length=1, examples=["StrongP@ssw0rd"])


class TokenPair(BaseModel):
    """Access + refresh token pair returned on login/refresh."""

    access_token: str = Field(..., description="Short-lived JWT access token.")
    refresh_token: str = Field(..., description="Long-lived JWT refresh token.")
    token_type: str = Field(default="bearer")


class LoginResponse(BaseModel):
    """Login result: tokens, or a 2FA challenge if two-step is enabled."""

    access_token: str | None = None
    refresh_token: str | None = None
    token_type: str = "bearer"
    requires_2fa: bool = False
    challenge_id: uuid.UUID | None = None


class RefreshRequest(BaseModel):
    """Request body for `POST /auth/refresh`."""

    refresh_token: str = Field(..., description="A previously issued, unrevoked refresh token.")


class LogoutRequest(BaseModel):
    """Request body for `POST /auth/logout`."""

    refresh_token: str = Field(..., description="The refresh token to revoke.")


class ForgotPasswordRequest(BaseModel):
    """Request body for `POST /auth/forgot-password`."""

    email: EmailStr = Field(..., examples=["jane.doe@example.com"])


class ResetPasswordRequest(BaseModel):
    """Request body for `POST /auth/reset-password`."""

    reset_token: str | None = Field(default=None, description="Token from the reset email link.")
    email: EmailStr | None = None
    code: str | None = Field(default=None, min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def require_token_or_code(self) -> ResetPasswordRequest:
        if self.reset_token or (self.email and self.code):
            return self
        raise ValueError("Provide reset_token or email and code.")


class ChangePasswordRequest(BaseModel):
    """Request body for `POST /auth/change-password`."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    """Response body for `POST /auth/register`."""

    user: UserRead
    verification_required: bool = True


class VerifyEmailRequest(BaseModel):
    """Request body for `POST /auth/verify-email`."""

    token: str | None = None
    email: EmailStr | None = None
    code: str | None = Field(default=None, min_length=6, max_length=6)

    @model_validator(mode="after")
    def require_token_or_code(self) -> VerifyEmailRequest:
        if self.token or (self.email and self.code):
            return self
        raise ValueError("Provide token or email and code.")


class ResendVerificationRequest(BaseModel):
    """Request body for `POST /auth/resend-verification`."""

    email: EmailStr


class LoginTwoFactorRequest(BaseModel):
    """Request body for `POST /auth/login/2fa`."""

    challenge_id: uuid.UUID
    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorCodeRequest(BaseModel):
    """Request body for confirming enable/disable of two-step verification."""

    code: str = Field(..., min_length=6, max_length=6)


class TwoFactorDisableStartRequest(BaseModel):
    """Request body for starting disable of two-step verification."""

    password: str = Field(..., min_length=1)
