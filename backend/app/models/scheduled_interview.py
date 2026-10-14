"""Human-scheduled interview, separate from the AI question/evaluation record."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, Index, String, Text
from app.database.types import GUID, JSONType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import HiringDecision, InterviewType
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ScheduledInterview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A calendar interview booked by a recruiter.

    This is not the `Interview` row written by the AI workflow. That table
    stores generated questions and transcript evaluations.

    Attributes:
        candidate_id: The candidate being interviewed.
        scheduled_at: Timezone-aware start time.
        interviewer_name: Display name used for conflict checks.
        interview_type: Phone, video, or onsite.
        notes: Optional recruiter note about the booking.
        feedback: Structured interviewer feedback, once submitted.
        decision: Final hire or no-hire decision, once recorded.
        created_by_id: Staff user who booked the interview.
    """

    __tablename__ = "scheduled_interviews"
    __table_args__ = (Index("ix_scheduled_interviews_interviewer_time", "interviewer_name", "scheduled_at"),)

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    interviewer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    interview_type: Mapped[InterviewType] = mapped_column(
        SAEnum(InterviewType, name="interview_type", create_type=False), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    decision: Mapped[HiringDecision | None] = mapped_column(
        SAEnum(HiringDecision, name="hiring_decision", create_type=False), nullable=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    candidate: Mapped["Candidate"] = relationship(back_populates="scheduled_interviews")
