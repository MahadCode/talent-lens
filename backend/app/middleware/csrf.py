"""Origin checks for browser mutating requests.

Auth is JWT in `Authorization`, not cookies, so classic CSRF tokens are
not used. This still rejects cross-site POSTs whose Origin is outside
the configured frontend/CORS allowlist.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class OriginGuardMiddleware(BaseHTTPMiddleware):
    """Block mutating browser requests from unknown origins in production."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if not settings.is_production or request.method in _SAFE_METHODS:
            return await call_next(request)

        origin = request.headers.get("origin")
        if not origin:
            return await call_next(request)

        allowed = {item.rstrip("/") for item in settings.cors_origins}
        if origin.rstrip("/") not in allowed:
            return JSONResponse(
                status_code=403,
                content={
                    "code": "csrf_origin_rejected",
                    "message": "Request origin is not allowed.",
                },
            )
        return await call_next(request)
