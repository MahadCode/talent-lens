"""Resume ORM model — stores uploaded resume files and extracted text."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Resume(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """An uploaded resume file associated with a candidate.

    Attributes:
        candidate_id: The candidate this resume belongs to.
        file_path: Filesystem/object-storage path of the original upload.
        original_filename: The filename as uploaded by the client.
        extracted_text: Raw text extracted from the resume (e.g. via a PDF
            text-extraction utility), fed into the Resume Parser Agent.
    """

    __tablename__ = "resumes"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidate: Mapped["Candidate"] = relationship(back_populates="resumes")
