"""Unit tests for email OTP hashing and login response shape."""

from __future__ import annotations

from app.core.security import generate_otp_code, hash_secret_value, secrets_match
from app.schemas.auth import LoginResponse, RegisterResponse, ResetPasswordRequest, VerifyEmailRequest
from app.schemas.user import UserRead


def test_otp_is_six_digits() -> None:
    code = generate_otp_code()
    assert len(code) == 6
    assert code.isdigit()


def test_secret_hash_roundtrip() -> None:
    code = "123456"
    hashed = hash_secret_value(code)
    assert secrets_match("123456", hashed)
    assert not secrets_match("000000", hashed)


def test_login_response_can_be_challenge_only() -> None:
    payload = LoginResponse(requires_2fa=True, challenge_id=None)
    assert payload.access_token is None
    assert payload.requires_2fa is True


def test_register_response_does_not_include_tokens() -> None:
    assert "tokens" not in RegisterResponse.model_fields


def test_user_read_includes_two_factor_flag() -> None:
    assert "two_factor_enabled" in UserRead.model_fields


def test_verify_accepts_token_or_code() -> None:
    VerifyEmailRequest(token="abc")
    VerifyEmailRequest(email="a@example.com", code="123456")


def test_reset_accepts_token_or_code() -> None:
    ResetPasswordRequest(reset_token="abc", new_password="newpass12")
    ResetPasswordRequest(email="a@example.com", code="123456", new_password="newpass12")
