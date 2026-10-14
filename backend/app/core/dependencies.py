"""Reusable FastAPI dependencies for authentication and authorization.

Routes depend on `get_current_user` (or one of the role-specific
`require_*` dependencies) rather than decoding JWTs or querying the user
table themselves, keeping auth concerns out of route handlers entirely.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TokenType, UserRole
from app.core.security import TokenPayloadError, decode_token
from app.database.session import get_db_session
from app.exceptions.errors import AuthorizationError
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Resolve the currently authenticated user from a bearer access token.

    Args:
        token: The raw JWT access token extracted from the Authorization header.
        session: The request-scoped async DB session.

    Returns:
        The authenticated, active `User`.

    Raises:
        HTTPException: 401 if the token is invalid/expired, or the user is
            missing/inactive.
    """

    try:
        payload = decode_token(token, expected_type=TokenType.ACCESS)
    except TokenPayloadError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_verified:
        raise AuthorizationError(
            "Verify your email before continuing.",
            error_code="email_not_verified",
        )
    return user


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Build a dependency that restricts access to a set of roles.

    Args:
        *allowed_roles: The roles permitted to access the protected route.

    Returns:
        A FastAPI dependency callable that returns the current user if
        authorized, or raises 403 otherwise.
    """

    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return _dependency


def require_admin() -> Callable[[User], User]:
    """Dependency restricting access to ADMIN users only.

    Returns:
        A FastAPI dependency callable.
    """

    return require_roles(UserRole.ADMIN)


def require_hr() -> Callable[[User], User]:
    """Dependency restricting access to ADMIN, HR_MANAGER, or RECRUITER users.

    Returns:
        A FastAPI dependency callable.
    """

    return require_roles(UserRole.ADMIN, UserRole.HR_MANAGER, UserRole.RECRUITER)


def require_recruiter() -> Callable[[User], User]:
    """Dependency restricting access to RECRUITER users (and ADMIN as superuser).

    Returns:
        A FastAPI dependency callable.
    """

    return require_roles(UserRole.ADMIN, UserRole.RECRUITER)


def require_candidate() -> Callable[[User], User]:
    """Dependency restricting access to CANDIDATE accounts.

    Returns:
        A FastAPI dependency callable.
    """

    return require_roles(UserRole.CANDIDATE)


# ---------------------------------------------------------------------------
# Repository and service factories.
#
# Routes depend on `get_*_service`, never on a repository or the raw DB
# session directly, keeping dependency injection consistent across the API
# layer and business logic swappable without touching route signatures.
# ---------------------------------------------------------------------------


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Provide a request-scoped `UserRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `UserRepository` bound to the current session.
    """

    return UserRepository(session)


def get_refresh_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> "RefreshTokenRepository":
    """Provide a request-scoped `RefreshTokenRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `RefreshTokenRepository` bound to the current session.
    """

    from app.repositories.refresh_token_repository import RefreshTokenRepository

    return RefreshTokenRepository(session)


def get_job_repository(session: AsyncSession = Depends(get_db_session)) -> "JobRepository":
    """Provide a request-scoped `JobRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `JobRepository` bound to the current session.
    """

    from app.repositories.job_repository import JobRepository

    return JobRepository(session)


def get_candidate_repository(session: AsyncSession = Depends(get_db_session)) -> "CandidateRepository":
    """Provide a request-scoped `CandidateRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `CandidateRepository` bound to the current session.
    """

    from app.repositories.candidate_repository import CandidateRepository

    return CandidateRepository(session)


def get_resume_repository(session: AsyncSession = Depends(get_db_session)) -> "ResumeRepository":
    """Provide a request-scoped `ResumeRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `ResumeRepository` bound to the current session.
    """

    from app.repositories.resume_repository import ResumeRepository

    return ResumeRepository(session)


def get_interview_repository(session: AsyncSession = Depends(get_db_session)) -> "InterviewRepository":
    """Provide a request-scoped `InterviewRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        An `InterviewRepository` bound to the current session.
    """

    from app.repositories.interview_repository import InterviewRepository

    return InterviewRepository(session)


def get_score_repository(session: AsyncSession = Depends(get_db_session)) -> "ScoreRepository":
    """Provide a request-scoped `ScoreRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `ScoreRepository` bound to the current session.
    """

    from app.repositories.score_repository import ScoreRepository

    return ScoreRepository(session)


def get_email_log_repository(session: AsyncSession = Depends(get_db_session)) -> "EmailLogRepository":
    """Provide a request-scoped `EmailLogRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        An `EmailLogRepository` bound to the current session.
    """

    from app.repositories.email_log_repository import EmailLogRepository

    return EmailLogRepository(session)


def get_email_challenge_repository(
    session: AsyncSession = Depends(get_db_session),
) -> "EmailChallengeRepository":
    from app.repositories.email_challenge_repository import EmailChallengeRepository

    return EmailChallengeRepository(session)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    refresh_token_repo: "RefreshTokenRepository" = Depends(get_refresh_token_repository),
    challenge_repo: "EmailChallengeRepository" = Depends(get_email_challenge_repository),
) -> "AuthService":
    """Provide a request-scoped `AuthService`."""

    from app.services.auth_service import AuthService

    return AuthService(
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        challenge_repo=challenge_repo,
    )


def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> "UserService":
    """Provide a request-scoped `UserService`.

    Args:
        user_repo: Injected `UserRepository`.

    Returns:
        A `UserService` instance.
    """

    from app.services.user_service import UserService

    return UserService(user_repo=user_repo)


def get_job_service(job_repo: "JobRepository" = Depends(get_job_repository)) -> "JobService":
    """Provide a request-scoped `JobService`.

    Args:
        job_repo: Injected `JobRepository`.

    Returns:
        A `JobService` instance.
    """

    from app.services.job_service import JobService

    return JobService(job_repo=job_repo)


def get_candidate_note_repository(
    session: AsyncSession = Depends(get_db_session),
) -> "CandidateNoteRepository":
    """Provide a request-scoped `CandidateNoteRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `CandidateNoteRepository` bound to the current session.
    """

    from app.repositories.candidate_note_repository import CandidateNoteRepository

    return CandidateNoteRepository(session)


def get_candidate_status_event_repository(
    session: AsyncSession = Depends(get_db_session),
) -> "CandidateStatusEventRepository":
    """Provide a request-scoped `CandidateStatusEventRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `CandidateStatusEventRepository` bound to the current session.
    """

    from app.repositories.candidate_status_event_repository import CandidateStatusEventRepository

    return CandidateStatusEventRepository(session)


def get_scheduled_interview_repository(
    session: AsyncSession = Depends(get_db_session),
) -> "ScheduledInterviewRepository":
    """Provide a request-scoped `ScheduledInterviewRepository`.

    Args:
        session: The request-scoped async DB session.

    Returns:
        A `ScheduledInterviewRepository` bound to the current session.
    """

    from app.repositories.scheduled_interview_repository import ScheduledInterviewRepository

    return ScheduledInterviewRepository(session)


def get_candidate_service(
    candidate_repo: "CandidateRepository" = Depends(get_candidate_repository),
    score_repo: "ScoreRepository" = Depends(get_score_repository),
    note_repo: "CandidateNoteRepository" = Depends(get_candidate_note_repository),
    event_repo: "CandidateStatusEventRepository" = Depends(get_candidate_status_event_repository),
    job_repo: "JobRepository" = Depends(get_job_repository),
) -> "CandidateService":
    """Provide a request-scoped `CandidateService`.

    Args:
        candidate_repo: Injected `CandidateRepository`.
        score_repo: Injected `ScoreRepository`.
        note_repo: Injected `CandidateNoteRepository`.
        event_repo: Injected `CandidateStatusEventRepository`.
        job_repo: Injected `JobRepository`.

    Returns:
        A `CandidateService` instance.
    """

    from app.services.candidate_service import CandidateService

    return CandidateService(
        candidate_repo=candidate_repo,
        score_repo=score_repo,
        note_repo=note_repo,
        event_repo=event_repo,
        job_repo=job_repo,
    )


def get_resume_service(
    resume_repo: "ResumeRepository" = Depends(get_resume_repository),
    candidate_repo: "CandidateRepository" = Depends(get_candidate_repository),
    job_repo: "JobRepository" = Depends(get_job_repository),
) -> "ResumeService":
    """Provide a request-scoped `ResumeService`.

    Args:
        resume_repo: Injected `ResumeRepository`.
        candidate_repo: Injected `CandidateRepository`.
        job_repo: Injected `JobRepository`.

    Returns:
        A `ResumeService` instance.
    """

    from app.services.resume_service import ResumeService

    return ResumeService(resume_repo=resume_repo, candidate_repo=candidate_repo, job_repo=job_repo)


def get_workflow_service(
    candidate_repo: "CandidateRepository" = Depends(get_candidate_repository),
    job_repo: "JobRepository" = Depends(get_job_repository),
    score_repo: "ScoreRepository" = Depends(get_score_repository),
    interview_repo: "InterviewRepository" = Depends(get_interview_repository),
    email_log_repo: "EmailLogRepository" = Depends(get_email_log_repository),
) -> "WorkflowService":
    """Provide a request-scoped `WorkflowService`.

    Args:
        candidate_repo: Injected `CandidateRepository`.
        job_repo: Injected `JobRepository`.
        score_repo: Injected `ScoreRepository`.
        interview_repo: Injected `InterviewRepository`.
        email_log_repo: Injected `EmailLogRepository`.

    Returns:
        A `WorkflowService` instance.
    """

    from app.services.workflow_service import WorkflowService

    return WorkflowService(
        candidate_repo=candidate_repo,
        job_repo=job_repo,
        score_repo=score_repo,
        interview_repo=interview_repo,
        email_log_repo=email_log_repo,
    )


def get_interview_service(
    candidate_repo: "CandidateRepository" = Depends(get_candidate_repository),
    interview_repo: "InterviewRepository" = Depends(get_interview_repository),
    job_repo: "JobRepository" = Depends(get_job_repository),
) -> "InterviewService":
    """Provide a request-scoped `InterviewService`.

    Args:
        candidate_repo: Injected `CandidateRepository`.
        interview_repo: Injected `InterviewRepository`.
        job_repo: Injected `JobRepository`.

    Returns:
        An `InterviewService` instance.
    """

    from app.services.interview_service import InterviewService

    return InterviewService(
        candidate_repo=candidate_repo, interview_repo=interview_repo, job_repo=job_repo
    )


def get_schedule_service(
    candidate_repo: "CandidateRepository" = Depends(get_candidate_repository),
    schedule_repo: "ScheduledInterviewRepository" = Depends(get_scheduled_interview_repository),
    event_repo: "CandidateStatusEventRepository" = Depends(get_candidate_status_event_repository),
) -> "ScheduleService":
    """Provide a request-scoped `ScheduleService`.

    Args:
        candidate_repo: Injected `CandidateRepository`.
        schedule_repo: Injected `ScheduledInterviewRepository`.
        event_repo: Injected `CandidateStatusEventRepository`.

    Returns:
        A `ScheduleService` instance.
    """

    from app.services.schedule_service import ScheduleService

    return ScheduleService(
        candidate_repo=candidate_repo, schedule_repo=schedule_repo, event_repo=event_repo
    )


def get_analytics_service(
    job_repo: "JobRepository" = Depends(get_job_repository),
    candidate_repo: "CandidateRepository" = Depends(get_candidate_repository),
    schedule_repo: "ScheduledInterviewRepository" = Depends(get_scheduled_interview_repository),
    event_repo: "CandidateStatusEventRepository" = Depends(get_candidate_status_event_repository),
) -> "AnalyticsService":
    """Provide a request-scoped `AnalyticsService`.

    Args:
        job_repo: Injected `JobRepository`.
        candidate_repo: Injected `CandidateRepository`.
        schedule_repo: Injected `ScheduledInterviewRepository`.
        event_repo: Injected `CandidateStatusEventRepository`.

    Returns:
        An `AnalyticsService` instance.
    """

    from app.services.analytics_service import AnalyticsService

    return AnalyticsService(
        job_repo=job_repo,
        candidate_repo=candidate_repo,
        schedule_repo=schedule_repo,
        event_repo=event_repo,
    )
