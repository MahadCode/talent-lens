"""Business logic for authentication and account security."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.core.config import Settings, get_settings
from app.core.constants import EmailChallengePurpose, TokenType, UserRole
from app.core.security import (
    TokenPayloadError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_link_token,
    generate_otp_code,
    hash_password,
    hash_secret_value,
    secrets_match,
    verify_password,
)
from app.exceptions.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    NotFoundError,
    RateLimitError,
)
from app.models.email_challenge import EmailChallenge
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.email_challenge_repository import EmailChallengeRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginResponse, TokenPair
from app.services.email_service import EmailService


class AuthService:
    """Coordinates registration, login, email challenges, and password resets."""

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        challenge_repo: EmailChallengeRepository,
        email_service: EmailService | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._challenge_repo = challenge_repo
        self._email_service = email_service or EmailService()
        self._settings = settings or get_settings()

    async def register(
        self,
        full_name: str,
        email: str,
        password: str,
        role: UserRole,
        company_name: str | None,
    ) -> User:
        existing = await self._user_repo.get_by_email(email)
        if existing is not None:
            raise ConflictError("A user with this email already exists.")

        user = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            company_name=company_name,
            is_verified=False,
            two_factor_enabled=False,
        )
        user = await self._user_repo.add(user)
        await self._issue_email_challenge(user, EmailChallengePurpose.EMAIL_VERIFY)
        return user

    async def login(self, email: str, password: str) -> LoginResponse:
        user = await self._user_repo.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")
        if not user.is_active:
            raise AuthenticationError("This account has been deactivated.")
        if not user.is_verified:
            raise AuthorizationError(
                "Verify your email before signing in.",
                error_code="email_not_verified",
            )

        if user.two_factor_enabled:
            challenge = await self._issue_email_challenge(user, EmailChallengePurpose.TWO_FACTOR_LOGIN)
            return LoginResponse(requires_2fa=True, challenge_id=challenge.id)

        user.last_login = datetime.now(timezone.utc)
        tokens = await self._issue_token_pair(user)
        return LoginResponse(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            token_type=tokens.token_type,
        )

    async def complete_login_2fa(self, challenge_id: uuid.UUID, code: str) -> TokenPair:
        challenge = await self._consume_challenge_by_id(
            challenge_id, code, EmailChallengePurpose.TWO_FACTOR_LOGIN
        )
        user = await self._user_repo.get_by_id(challenge.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive.")
        user.last_login = datetime.now(timezone.utc)
        return await self._issue_token_pair(user)

    async def verify_email(self, token: str | None, email: str | None, code: str | None) -> User:
        challenge = await self._resolve_challenge(
            purpose=EmailChallengePurpose.EMAIL_VERIFY,
            token=token,
            email=email,
            code=code,
        )
        user = await self._user_repo.get_by_id(challenge.user_id)
        if user is None:
            raise NotFoundError("User not found.")
        user.is_verified = True
        return user

    async def resend_verification(self, email: str) -> None:
        user = await self._user_repo.get_by_email(email)
        if user is None or user.is_verified or not user.is_active:
            return
        await self._issue_email_challenge(user, EmailChallengePurpose.EMAIL_VERIFY)

    async def refresh(self, refresh_token: str) -> TokenPair:
        try:
            payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        except TokenPayloadError as exc:
            raise AuthenticationError("Invalid or expired refresh token.") from exc

        stored_token = await self._refresh_token_repo.get_by_jti(payload["jti"])
        if stored_token is None or stored_token.is_revoked:
            raise AuthenticationError("Refresh token has been revoked.")

        user = await self._user_repo.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthenticationError("User not found or inactive.")
        if not user.is_verified:
            raise AuthorizationError(
                "Verify your email before continuing.",
                error_code="email_not_verified",
            )

        await self._refresh_token_repo.revoke(stored_token)
        return await self._issue_token_pair(user)

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token, expected_type=TokenType.REFRESH)
        except TokenPayloadError as exc:
            raise AuthenticationError("Invalid refresh token.") from exc

        stored_token = await self._refresh_token_repo.get_by_jti(payload["jti"])
        if stored_token is not None:
            await self._refresh_token_repo.revoke(stored_token)

    async def request_password_reset(self, email: str) -> None:
        user = await self._user_repo.get_by_email(email)
        if user is None or not user.is_active:
            return
        await self._issue_email_challenge(user, EmailChallengePurpose.PASSWORD_RESET)

    async def reset_password(
        self,
        new_password: str,
        reset_token: str | None = None,
        email: str | None = None,
        code: str | None = None,
    ) -> None:
        challenge = await self._resolve_challenge(
            purpose=EmailChallengePurpose.PASSWORD_RESET,
            token=reset_token,
            email=email,
            code=code,
        )
        user = await self._user_repo.get_by_id(challenge.user_id)
        if user is None:
            raise NotFoundError("User not found.")
        user.hashed_password = hash_password(new_password)
        await self._refresh_token_repo.revoke_all_for_user(user.id)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect.")
        user.hashed_password = hash_password(new_password)
        await self._refresh_token_repo.revoke_all_for_user(user.id)

    async def request_two_factor_enable(self, user: User) -> None:
        if user.two_factor_enabled:
            raise ConflictError("Two-step verification is already on.")
        await self._issue_email_challenge(user, EmailChallengePurpose.TWO_FACTOR_ENABLE)

    async def confirm_two_factor_enable(self, user: User, code: str) -> None:
        challenge = await self._challenge_repo.get_active_for_user(
            user.id, EmailChallengePurpose.TWO_FACTOR_ENABLE.value
        )
        if challenge is None:
            raise AuthenticationError("No two-step verification request is pending.")
        await self._consume_existing(challenge, code)
        user.two_factor_enabled = True

    async def request_two_factor_disable(self, user: User, password: str) -> None:
        if not user.two_factor_enabled:
            raise ConflictError("Two-step verification is already off.")
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect.")
        await self._issue_email_challenge(user, EmailChallengePurpose.TWO_FACTOR_DISABLE)

    async def confirm_two_factor_disable(self, user: User, code: str) -> None:
        challenge = await self._challenge_repo.get_active_for_user(
            user.id, EmailChallengePurpose.TWO_FACTOR_DISABLE.value
        )
        if challenge is None:
            raise AuthenticationError("No two-step disable request is pending.")
        await self._consume_existing(challenge, code)
        user.two_factor_enabled = False

    async def _issue_email_challenge(self, user: User, purpose: EmailChallengePurpose) -> EmailChallenge:
        window = timedelta(minutes=self._settings.email_send_window_minutes)
        recent = await self._challenge_repo.count_recent(user.id, purpose.value, window)
        if recent >= self._settings.email_send_limit:
            raise RateLimitError("Too many emails sent. Wait a few minutes and try again.")

        await self._challenge_repo.consume_open_for_user(user.id, purpose.value)
        code = generate_otp_code()
        link_token = generate_link_token() if purpose in {
            EmailChallengePurpose.EMAIL_VERIFY,
            EmailChallengePurpose.PASSWORD_RESET,
        } else None
        minutes = (
            self._settings.email_link_expire_minutes
            if purpose in {EmailChallengePurpose.EMAIL_VERIFY, EmailChallengePurpose.PASSWORD_RESET}
            else self._settings.email_otp_expire_minutes
        )
        challenge = EmailChallenge(
            user_id=user.id,
            purpose=purpose.value,
            code_hash=hash_secret_value(code),
            link_token_hash=hash_secret_value(link_token) if link_token else None,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=minutes),
            attempt_count=0,
        )
        challenge = await self._challenge_repo.add(challenge)
        await self._deliver(user, purpose, code, link_token)
        return challenge

    async def _deliver(
        self,
        user: User,
        purpose: EmailChallengePurpose,
        code: str,
        link_token: str | None,
    ) -> None:
        origin = self._settings.frontend_url.rstrip("/")
        if purpose is EmailChallengePurpose.EMAIL_VERIFY:
            link = f"{origin}/verify-email?token={link_token}"
            await self._email_service.send_verification(user.email, code, link)
            return
        if purpose is EmailChallengePurpose.PASSWORD_RESET:
            link = f"{origin}/reset-password?token={link_token}"
            await self._email_service.send_password_reset(user.email, code, link)
            return
        await self._email_service.send_two_factor(user.email, code)

    async def _resolve_challenge(
        self,
        purpose: EmailChallengePurpose,
        token: str | None,
        email: str | None,
        code: str | None,
    ) -> EmailChallenge:
        if token:
            challenge = await self._challenge_repo.get_active_by_link_hash(hash_secret_value(token))
            if challenge is None or challenge.purpose != purpose.value:
                raise AuthenticationError("Invalid or expired link.")
            now = datetime.now(timezone.utc)
            expires = challenge.expires_at
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=timezone.utc)
            if expires < now:
                await self._mark_consumed(challenge)
                raise AuthenticationError("This link has expired.")
            await self._mark_consumed(challenge)
            return challenge

        if not email or not code:
            raise AuthenticationError("Invalid or expired code.")
        user = await self._user_repo.get_by_email(email)
        if user is None:
            raise AuthenticationError("Invalid or expired code.")
        challenge = await self._challenge_repo.get_active_for_user(user.id, purpose.value)
        if challenge is None:
            raise AuthenticationError("Invalid or expired code.")
        await self._consume_existing(challenge, code)
        return challenge

    async def _consume_challenge_by_id(
        self,
        challenge_id: uuid.UUID,
        code: str,
        purpose: EmailChallengePurpose,
    ) -> EmailChallenge:
        challenge = await self._challenge_repo.get_active_by_id(challenge_id)
        if challenge is None or challenge.purpose != purpose.value:
            raise AuthenticationError("Invalid or expired code.")
        await self._consume_existing(challenge, code)
        return challenge

    async def _consume_existing(self, challenge: EmailChallenge, code: str) -> None:
        now = datetime.now(timezone.utc)
        expires = challenge.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            await self._mark_consumed(challenge)
            raise AuthenticationError("This code has expired.")
        challenge.attempt_count += 1
        if challenge.attempt_count > self._settings.email_otp_max_attempts:
            await self._mark_consumed(challenge)
            raise RateLimitError("Too many incorrect codes. Request a new one.")
        if not secrets_match(code.strip(), challenge.code_hash):
            await self._challenge_repo._session.flush()
            raise AuthenticationError("Invalid or expired code.")
        await self._mark_consumed(challenge)

    async def _mark_consumed(self, challenge: EmailChallenge) -> None:
        challenge.consumed_at = datetime.now(timezone.utc)
        await self._challenge_repo._session.flush()

    async def _issue_token_pair(self, user: User) -> TokenPair:
        access_token = create_access_token(user_id=str(user.id), role=user.role.value)
        refresh_token_str = create_refresh_token(user_id=str(user.id))
        payload = decode_token(refresh_token_str, expected_type=TokenType.REFRESH)
        refresh_token_record = RefreshToken(
            user_id=user.id,
            jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        )
        await self._refresh_token_repo.add(refresh_token_record)
        return TokenPair(access_token=access_token, refresh_token=refresh_token_str)
