"""Declarative base class and shared mixins for all SQLAlchemy models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.database.types import GUID


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


class UUIDPrimaryKeyMixin:
    """Mixin providing a UUID primary key column named `id`."""

    id: Mapped[uuid.UUID] = mapped_column(
        GUID, primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Mixin providing `created_at` / `updated_at` timestamp columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
