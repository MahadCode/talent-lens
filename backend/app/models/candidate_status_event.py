"""Audit trail of candidate pipeline status changes."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, Index
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import CandidateStatus
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateStatusEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One recorded transition of a candidate's pipeline status.

    Attributes:
        candidate_id: The candidate whose status changed.
        actor_id: The staff user who made the change.
        from_status: Status before the change.
        to_status: Status after the change.
    """

    __tablename__ = "candidate_status_events"
    __table_args__ = (Index("ix_candidate_status_events_candidate_created", "candidate_id", "created_at"),)

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[CandidateStatus] = mapped_column(
        SAEnum(CandidateStatus, name="candidate_status", create_type=False), nullable=False
    )
    to_status: Mapped[CandidateStatus] = mapped_column(
        SAEnum(CandidateStatus, name="candidate_status", create_type=False), nullable=False
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="status_events")
