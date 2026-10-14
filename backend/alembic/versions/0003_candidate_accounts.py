"""candidate user accounts and owned applications

Revision ID: 0003_candidate_accounts
Revises: 0002_pipeline
Create Date: 2026-11-05

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_candidate_accounts"
down_revision: Union[str, None] = "0002_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the CANDIDATE role and link applications to user accounts."""

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'CANDIDATE'")

    op.add_column(
        "candidates",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_candidates_user_id_users",
        "candidates",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_candidates_user_id", "candidates", ["user_id"])
    op.create_unique_constraint("uq_candidates_user_job", "candidates", ["user_id", "job_id"])


def downgrade() -> None:
    """Remove the candidate-account link. The CANDIDATE enum value is left in place."""

    op.drop_constraint("uq_candidates_user_job", "candidates", type_="unique")
    op.drop_index("ix_candidates_user_id", table_name="candidates")
    op.drop_constraint("fk_candidates_user_id_users", "candidates", type_="foreignkey")
    op.drop_column("candidates", "user_id")
