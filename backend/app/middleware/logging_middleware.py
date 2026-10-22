"""ASGI middleware that logs every incoming request and its outcome."""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__, component="request_logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs method, path, status code, duration, and a request id per request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Log the request/response cycle and attach a request id.

        Args:
            request: The incoming ASGI request.
            call_next: The next handler in the middleware chain.

        Returns:
            The response produced by downstream handlers.
        """

        request_id = str(uuid.uuid4())
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "%s %s -> %s (%.2fms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
            },
        )
        return response
