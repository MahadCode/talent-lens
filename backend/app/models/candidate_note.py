"""Private recruiter notes attached to a candidate."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CandidateNote(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A note visible only to hiring staff.

    Attributes:
        candidate_id: The candidate this note is about.
        author_id: The staff user who wrote the note.
        body: The note text.
    """

    __tablename__ = "candidate_notes"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="notes")
