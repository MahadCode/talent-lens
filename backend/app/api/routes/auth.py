"""Authentication endpoints: registration, login, tokens, password management."""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, status

from app.core.dependencies import get_auth_service, get_current_user, get_user_service
from app.exceptions.errors import ValidationAppError
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LoginResponse,
    LoginTwoFactorRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TokenPair,
    TwoFactorCodeRequest,
    TwoFactorDisableStartRequest,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse
from app.schemas.user import ProfileImageResponse, ProfileUpdate, UserRead
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])

_MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024
_ALLOWED_IMAGE_CONTENT_TYPES = {"image/png", "image/jpeg", "image/webp"}


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a staff or candidate account and emails a verification code. "
    "The account cannot sign in until the email is verified. Pass role=CANDIDATE to "
    "register as an applicant.",
    responses={409: {"description": "A user with this email already exists."}},
)
async def register(
    payload: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
) -> RegisterResponse:
    """Register a new user account without issuing tokens."""

    user = await auth_service.register(
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
        company_name=payload.company_name,
    )
    return RegisterResponse(user=UserRead.model_validate(user), verification_required=True)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Log in",
    description="Authenticates a user by email and password. Unverified accounts are rejected. "
    "If two-step verification is on, returns a challenge instead of tokens.",
    responses={
        401: {"description": "Invalid credentials or inactive account."},
        403: {"description": "Email is not verified."},
    },
)
async def login(payload: LoginRequest, auth_service: AuthService = Depends(get_auth_service)) -> LoginResponse:
    """Authenticate a user; may require an email OTP before tokens are issued."""

    return await auth_service.login(email=payload.email, password=payload.password)


@router.post(
    "/refresh",
    response_model=TokenPair,
    summary="Refresh an access token",
    description="Exchanges a valid, unrevoked refresh token for a new access/refresh token pair "
    "(refresh token rotation: the old refresh token is revoked).",
    responses={401: {"description": "Invalid, expired, or revoked refresh token."}},
)
async def refresh(
    payload: RefreshRequest, auth_service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    """Rotate a refresh token for a new token pair.

    Args:
        payload: The refresh token to exchange.
        auth_service: Injected `AuthService`.

    Returns:
        A new access/refresh token pair.
    """

    return await auth_service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Log out",
    description="Revokes the given refresh token, ending that session.",
)
async def logout(
    payload: LogoutRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """Revoke a refresh token.

    Args:
        payload: The refresh token to revoke.
        auth_service: Injected `AuthService`.

    Returns:
        A confirmation message.
    """

    await auth_service.logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request a password reset",
    description="Issues a password reset token if the email matches an account. Always returns "
    "a generic success message, regardless of whether the email exists, to avoid leaking "
    "which emails are registered.",
)
async def forgot_password(
    payload: ForgotPasswordRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """Request a password reset token.

    Args:
        payload: The email address requesting a reset.
        auth_service: Injected `AuthService`.

    Returns:
        A generic confirmation message.
    """

    await auth_service.request_password_reset(payload.email)
    return MessageResponse(message="If that email is registered, a reset link has been sent.")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email",
    description="Confirms an email address with the mailed code or link token.",
)
async def verify_email(
    payload: VerifyEmailRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    await auth_service.verify_email(token=payload.token, email=payload.email, code=payload.code)
    return MessageResponse(message="Email verified. You can sign in now.")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend verification email",
)
async def resend_verification(
    payload: ResendVerificationRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    await auth_service.resend_verification(payload.email)
    return MessageResponse(message="If that email needs verification, a new code has been sent.")


@router.post(
    "/login/2fa",
    response_model=TokenPair,
    summary="Complete two-step login",
)
async def login_2fa(
    payload: LoginTwoFactorRequest, auth_service: AuthService = Depends(get_auth_service)
) -> TokenPair:
    return await auth_service.complete_login_2fa(payload.challenge_id, payload.code)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password with a reset token",
    description="Sets a new password using a valid password-reset token issued via forgot-password.",
    responses={401: {"description": "Invalid or expired reset token."}},
)
async def reset_password(
    payload: ResetPasswordRequest, auth_service: AuthService = Depends(get_auth_service)
) -> MessageResponse:
    """Reset a password using a reset token.

    Args:
        payload: The reset token and new password.
        auth_service: Injected `AuthService`.

    Returns:
        A confirmation message.
    """

    await auth_service.reset_password(
        new_password=payload.new_password,
        reset_token=payload.reset_token,
        email=payload.email,
        code=payload.code,
    )
    return MessageResponse(message="Password has been reset successfully.")


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password (authenticated)",
    description="Changes the current user's password after verifying their current password. "
    "Revokes all existing refresh tokens, requiring re-login on other devices.",
    responses={401: {"description": "Current password is incorrect, or not authenticated."}},
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Change the authenticated user's password.

    Args:
        payload: The current and new passwords.
        current_user: The authenticated user.
        auth_service: Injected `AuthService`.

    Returns:
        A confirmation message.
    """

    await auth_service.change_password(current_user, payload.current_password, payload.new_password)
    return MessageResponse(message="Password changed successfully.")


@router.post("/2fa/enable", response_model=MessageResponse, summary="Start enabling email 2-step")
async def enable_2fa(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.request_two_factor_enable(current_user)
    return MessageResponse(message="We sent a confirmation code to your email.")


@router.post("/2fa/confirm", response_model=UserRead, summary="Confirm enabling email 2-step")
async def confirm_2fa(
    payload: TwoFactorCodeRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    await auth_service.confirm_two_factor_enable(current_user, payload.code)
    return UserRead.model_validate(current_user)


@router.post("/2fa/disable", response_model=MessageResponse, summary="Start disabling email 2-step")
async def disable_2fa(
    payload: TwoFactorDisableStartRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    await auth_service.request_two_factor_disable(current_user, payload.password)
    return MessageResponse(message="We sent a confirmation code to your email.")


@router.post("/2fa/disable/confirm", response_model=UserRead, summary="Confirm disabling email 2-step")
async def confirm_disable_2fa(
    payload: TwoFactorCodeRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRead:
    await auth_service.confirm_two_factor_disable(current_user, payload.code)
    return UserRead.model_validate(current_user)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the current authenticated user",
    description="Returns the profile of the user identified by the bearer access token.",
)
async def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the authenticated user's own profile.

    Args:
        current_user: The authenticated user.

    Returns:
        The user's public profile.
    """

    return UserRead.model_validate(current_user)


@router.put(
    "/profile",
    response_model=UserRead,
    summary="Update own profile",
    description="Updates the authenticated user's own full name and/or company name.",
)
async def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> UserRead:
    """Update the authenticated user's profile.

    Args:
        payload: Fields to update.
        current_user: The authenticated user.
        user_service: Injected `UserService`.

    Returns:
        The updated user profile.
    """

    updated = await user_service.update_profile(current_user, payload)
    return UserRead.model_validate(updated)


@router.post(
    "/profile-image",
    response_model=ProfileImageResponse,
    summary="Upload a profile image",
    description="Uploads a new profile image (PNG/JPEG/WebP, max 5MB) for the authenticated user.",
    responses={422: {"description": "Invalid file type or file too large."}},
)
async def upload_profile_image(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> ProfileImageResponse:
    """Upload and set the authenticated user's profile image.

    Args:
        file: The uploaded image file.
        current_user: The authenticated user.
        user_service: Injected `UserService`.

    Returns:
        The stored image path/URL.

    Raises:
        ValidationAppError: If the file type is unsupported or the file
            exceeds the maximum allowed size.
    """

    if file.content_type not in _ALLOWED_IMAGE_CONTENT_TYPES:
        raise ValidationAppError("Only PNG, JPEG, or WebP images are supported.")

    contents = await file.read()
    if len(contents) > _MAX_PROFILE_IMAGE_BYTES:
        raise ValidationAppError("Profile image must be 5MB or smaller.")

    from pathlib import Path
    import uuid as uuid_module

    from app.core.config import get_settings

    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / "profile_images"
    upload_dir.mkdir(parents=True, exist_ok=True)
    extension = Path(file.filename or "image").suffix or ".png"
    destination = upload_dir / f"{uuid_module.uuid4()}{extension}"
    destination.write_bytes(contents)

    await user_service.set_profile_image(current_user, str(destination))
    return ProfileImageResponse(profile_image=str(destination))
