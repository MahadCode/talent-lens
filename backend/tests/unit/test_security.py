"""Unit tests for password hashing and JWT primitives (no DB, no network)."""

from __future__ import annotations

import pytest

from app.core.constants import TokenType
from app.core.security import (
    TokenPayloadError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip() -> None:
    """A password should verify against its own hash and reject a wrong one."""

    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip() -> None:
    """An access token should decode back to its original subject and role."""

    token = create_access_token(user_id="user-123", role="ADMIN")
    payload = decode_token(token, expected_type=TokenType.ACCESS)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "ADMIN"
    assert payload["type"] == TokenType.ACCESS.value


def test_refresh_token_rejected_as_access_token() -> None:
    """Decoding a refresh token as if it were an access token should fail."""

    refresh_token = create_refresh_token(user_id="user-123")
    with pytest.raises(TokenPayloadError):
        decode_token(refresh_token, expected_type=TokenType.ACCESS)


def test_malformed_token_raises() -> None:
    """A garbage token string should raise `TokenPayloadError`."""

    with pytest.raises(TokenPayloadError):
        decode_token("not-a-real-token", expected_type=TokenType.ACCESS)
