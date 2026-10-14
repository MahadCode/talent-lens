"""EmailLog ORM model — audit trail of generated (not sent) candidate emails."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_agents.utils.schemas import EmailType
from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EmailLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A record of an email drafted by the Email Agent for a candidate.

    This table is an audit log of generated content; it does not imply the
    email was actually dispatched by any mail transport.

    Attributes:
        candidate_id: The candidate this email was drafted for.
        email_type: Category of email (shortlist, rejection, interview
            invitation).
        subject: The generated email subject line.
        body: The generated email body.
    """

    __tablename__ = "email_logs"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    email_type: Mapped[EmailType] = mapped_column(
        SAEnum(EmailType, name="email_log_type", create_type=False), nullable=False
    )
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="email_logs")
