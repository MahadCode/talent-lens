"""pipeline notes, audit events, schedules, and stored match evidence

Revision ID: 0002_pipeline
Revises: 0001_initial
Create Date: 2026-11-05

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_pipeline"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

candidate_status_enum = postgresql.ENUM(
    "NEW",
    "PARSED",
    "SHORTLISTED",
    "MANUAL_REVIEW",
    "REJECTED",
    "INTERVIEWING",
    "HIRED",
    "NOT_HIRED",
    name="candidate_status",
    create_type=False,
)

interview_type_enum = postgresql.ENUM(
    "PHONE",
    "VIDEO",
    "ONSITE",
    name="interview_type",
    create_type=False,
)

hiring_decision_enum = postgresql.ENUM(
    "HIRED",
    "NOT_HIRED",
    name="hiring_decision",
    create_type=False,
)


def upgrade() -> None:
    """Add pipeline columns and the note, audit, and schedule tables."""

    bind = op.get_bind()
    interview_type_enum.create(bind, checkfirst=True)
    hiring_decision_enum.create(bind, checkfirst=True)

    op.add_column("candidates", sa.Column("matching_result", postgresql.JSONB(), nullable=True))
    op.add_column(
        "candidates",
        sa.Column("score_overridden", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("jobs", sa.Column("extracted_requirements", postgresql.JSONB(), nullable=True))

    op.create_table(
        "candidate_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_candidate_notes_candidate_id", "candidate_notes", ["candidate_id"])

    op.create_table(
        "candidate_status_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_status", candidate_status_enum, nullable=False),
        sa.Column("to_status", candidate_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_candidate_status_events_candidate_created",
        "candidate_status_events",
        ["candidate_id", "created_at"],
    )

    op.create_table(
        "scheduled_interviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "candidate_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("candidates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interviewer_name", sa.String(255), nullable=False),
        sa.Column("interview_type", interview_type_enum, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("feedback", postgresql.JSONB(), nullable=True),
        sa.Column("decision", hiring_decision_enum, nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scheduled_interviews_candidate_id", "scheduled_interviews", ["candidate_id"])
    op.create_index(
        "ix_scheduled_interviews_interviewer_time",
        "scheduled_interviews",
        ["interviewer_name", "scheduled_at"],
    )


def downgrade() -> None:
    """Remove pipeline tables and columns added by this migration."""

    op.drop_index("ix_scheduled_interviews_interviewer_time", table_name="scheduled_interviews")
    op.drop_index("ix_scheduled_interviews_candidate_id", table_name="scheduled_interviews")
    op.drop_table("scheduled_interviews")

    op.drop_index("ix_candidate_status_events_candidate_created", table_name="candidate_status_events")
    op.drop_table("candidate_status_events")

    op.drop_index("ix_candidate_notes_candidate_id", table_name="candidate_notes")
    op.drop_table("candidate_notes")

    op.drop_column("jobs", "extracted_requirements")
    op.drop_column("candidates", "score_overridden")
    op.drop_column("candidates", "matching_result")

    bind = op.get_bind()
    hiring_decision_enum.drop(bind, checkfirst=True)
    interview_type_enum.drop(bind, checkfirst=True)
