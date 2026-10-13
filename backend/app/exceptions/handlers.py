"""Global exception handlers, registered once on the FastAPI app in `main.py`.

Ensures every error — expected domain errors, request validation errors,
and unexpected exceptions — is returned as a consistent JSON envelope
matching `schemas.common.ErrorResponse`.
"""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger
from app.exceptions.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    EmailDeliveryError,
    NotFoundError,
    RateLimitError,
    ValidationAppError,
    WorkflowExecutionError,
)

logger = get_logger(__name__, component="exception_handlers")

_STATUS_BY_ERROR_TYPE: dict[type[AppError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    ValidationAppError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    AuthenticationError: status.HTTP_401_UNAUTHORIZED,
    AuthorizationError: status.HTTP_403_FORBIDDEN,
    RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    EmailDeliveryError: status.HTTP_503_SERVICE_UNAVAILABLE,
    WorkflowExecutionError: status.HTTP_502_BAD_GATEWAY,
}


def _error_body(error_code: str, message: str, details: dict | None = None) -> dict:
    """Build the standard error response body.

    Args:
        error_code: Machine-readable error code.
        message: Human-readable message.
        details: Optional additional structured details.

    Returns:
        A dict matching `schemas.common.ErrorResponse`.
    """

    return {"error": error_code, "message": message, "details": details}


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        """Handle any known `AppError` subclass with the correct status code."""

        status_code = _STATUS_BY_ERROR_TYPE.get(type(exc), status.HTTP_400_BAD_REQUEST)
        logger.warning("Handled application error: %s", exc.message, extra={"error_code": exc.error_code})
        return JSONResponse(
            status_code=status_code,
            content=_error_body(exc.error_code, exc.message),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle FastAPI/Pydantic request validation failures."""

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body("request_validation_error", "Invalid request.", {"errors": exc.errors()}),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """Handle any exception not otherwise matched, without leaking internals."""

        logger.exception("Unhandled exception while processing request.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("internal_server_error", "An unexpected error occurred."),
        )
