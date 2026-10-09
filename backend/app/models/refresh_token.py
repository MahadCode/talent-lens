"""RefreshToken ORM model — tracks issued refresh tokens for revocation/rotation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A persisted record of an issued JWT refresh token.

    Storing the token's `jti` (JWT ID) — never the token itself — lets the
    backend revoke individual sessions and enforce refresh-token rotation
    (a used token is marked `is_revoked` and a new one is issued) without
    needing to persist any secret material.

    Attributes:
        user_id: The user this refresh token was issued to.
        jti: The unique JWT ID claim of the issued token.
        is_revoked: Whether this token has been revoked (via logout,
            rotation, or administrative action).
        expires_at: When this token expires, mirrored from the JWT `exp`
            claim for fast lookups without decoding the token.
    """

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
