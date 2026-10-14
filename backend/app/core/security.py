"""Password hashing and JWT encode/decode primitives.

This module contains only cryptographic primitives — no database access
and no business logic — so it can be unit tested in isolation and reused
by both `AuthService` and FastAPI dependencies.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.constants import TokenType

_pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenPayloadError(Exception):
    """Raised when a JWT is invalid, expired, or missing required claims."""


def hash_secret_value(value: str) -> str:
    """HMAC-SHA256 a one-time code or link token with the JWT secret as pepper."""

    settings = get_settings()
    return hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        value.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def secrets_match(plain_value: str, hashed_value: str) -> bool:
    """Constant-time compare of a submitted code/token against a stored hash."""

    return hmac.compare_digest(hash_secret_value(plain_value), hashed_value)


def generate_otp_code() -> str:
    """Return a cryptographically random 6-digit code."""

    return f"{secrets.randbelow(1_000_000):06d}"


def generate_link_token() -> str:
    """Return a URL-safe token for verify/reset links."""

    return secrets.token_urlsafe(32)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password with bcrypt.

    Args:
        plain_password: The user-supplied plaintext password.

    Returns:
        A bcrypt password hash safe to persist.
    """

    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: The user-supplied plaintext password.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        True if the password matches the hash, False otherwise.
    """

    return _pwd_context.verify(plain_password, hashed_password)


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT with standard claims.

    Args:
        subject: The token subject, typically the user's id as a string.
        token_type: The kind of token being created.
        expires_delta: How long until the token expires.
        extra_claims: Additional claims to embed (e.g. role, jti).

    Returns:
        An encoded JWT string.
    """

    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived JWT access token for an authenticated user.

    Args:
        user_id: The authenticated user's id.
        role: The user's role, embedded as a claim for fast authorization
            checks without a database round-trip.

    Returns:
        An encoded JWT access token.
    """

    settings = get_settings()
    return _create_token(
        subject=user_id,
        token_type=TokenType.ACCESS,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"role": role},
    )


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived JWT refresh token for an authenticated user.

    Args:
        user_id: The authenticated user's id.

    Returns:
        An encoded JWT refresh token. The token's `jti` claim should be
        persisted (see `RefreshToken` model) so it can be revoked/rotated.
    """

    settings = get_settings()
    return _create_token(
        subject=user_id,
        token_type=TokenType.REFRESH,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def create_password_reset_token(user_id: str) -> str:
    """Create a short-lived JWT used to authorize a single password reset.

    Args:
        user_id: The id of the user requesting a password reset.

    Returns:
        An encoded JWT password-reset token.
    """

    settings = get_settings()
    return _create_token(
        subject=user_id,
        token_type=TokenType.PASSWORD_RESET,
        expires_delta=timedelta(minutes=settings.password_reset_token_expire_minutes),
    )


def decode_token(token: str, expected_type: TokenType) -> dict[str, Any]:
    """Decode and validate a JWT, enforcing the expected token type.

    Args:
        token: The encoded JWT string.
        expected_type: The token type this call site expects (access,
            refresh, or password_reset). Prevents e.g. a refresh token
            being replayed as an access token.

    Returns:
        The decoded JWT claims.

    Raises:
        TokenPayloadError: If the token is malformed, expired, or of the
            wrong type.
    """

    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise TokenPayloadError("Token is invalid or expired.") from exc

    if payload.get("type") != expected_type.value:
        raise TokenPayloadError(f"Expected a {expected_type.value} token.")

    return payload
