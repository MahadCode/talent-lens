"""Score ORM model — stores per-dimension and total candidate scores."""

from __future__ import annotations

import uuid

from sqlalchemy import Float, ForeignKey, Text
from app.database.types import GUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Score(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A scoring result produced by the Candidate Scoring Agent.

    Attributes:
        candidate_id: The candidate this score belongs to.
        skills_score: Score for the skills dimension (0-100).
        experience_score: Score for the experience dimension (0-100).
        projects_score: Score for the projects dimension (0-100).
        education_score: Score for the education dimension (0-100).
        certifications_score: Score for the certifications dimension (0-100).
        total_score: Weighted total score (0-100).
        reasoning: LLM-generated rationale for the scores.
    """

    __tablename__ = "scores"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        GUID, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    skills_score: Mapped[float] = mapped_column(Float, nullable=False)
    experience_score: Mapped[float] = mapped_column(Float, nullable=False)
    projects_score: Mapped[float] = mapped_column(Float, nullable=False)
    education_score: Mapped[float] = mapped_column(Float, nullable=False)
    certifications_score: Mapped[float] = mapped_column(Float, nullable=False)
    total_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    candidate: Mapped["Candidate"] = relationship(back_populates="scores")
