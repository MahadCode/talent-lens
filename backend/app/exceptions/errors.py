"""Custom exception hierarchy for the backend.

Services and routes raise these instead of generic `Exception`/`HTTPException`
so the global handlers in `handlers.py` can map each type to a consistent
JSON error response and the correct HTTP status code.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application-raised errors.

    Attributes:
        message: Human-readable error message.
        error_code: Machine-readable error code returned in the response body.
    """

    error_code: str = "app_error"

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """Initialize the error.

        Args:
            message: Human-readable error message.
            error_code: Optional override for the machine-readable code.
        """

        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    error_code = "not_found"


class ConflictError(AppError):
    """Raised when an operation would violate a uniqueness/state constraint."""

    error_code = "conflict"


class ValidationAppError(AppError):
    """Raised for domain-level validation failures not caught by Pydantic."""

    error_code = "validation_error"


class AuthenticationError(AppError):
    """Raised when credentials are missing or invalid."""

    error_code = "authentication_error"


class AuthorizationError(AppError):
    """Raised when an authenticated user lacks permission for an action."""

    error_code = "authorization_error"


class RateLimitError(AppError):
    """Raised when an email/OTP action is attempted too often."""

    error_code = "rate_limited"


class EmailDeliveryError(AppError):
    """Raised when a transactional email cannot be delivered."""

    error_code = "email_delivery_error"


class WorkflowExecutionError(AppError):
    """Raised when the LangGraph hiring workflow fails to execute."""

    error_code = "workflow_execution_error"
