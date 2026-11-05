"""email verification, password-reset challenges, and two-factor flag

Revision ID: 0004_email_auth
Revises: 0003_candidate_accounts
Create Date: 2026-11-06

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_email_auth"
down_revision: Union[str, None] = "0003_candidate_accounts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add two-factor flag, grandfather existing users, create email challenges."""

    op.add_column(
        "users",
        sa.Column("two_factor_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(sa.text("UPDATE users SET is_verified = true"))

    op.create_table(
        "email_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("link_token_hash", sa.String(64), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_email_challenges_user_id", "email_challenges", ["user_id"])
    op.create_index("ix_email_challenges_purpose", "email_challenges", ["purpose"])
    op.create_index("ix_email_challenges_link_token_hash", "email_challenges", ["link_token_hash"])


def downgrade() -> None:
    """Drop email challenges and the two-factor column."""

    op.drop_index("ix_email_challenges_link_token_hash", table_name="email_challenges")
    op.drop_index("ix_email_challenges_purpose", table_name="email_challenges")
    op.drop_index("ix_email_challenges_user_id", table_name="email_challenges")
    op.drop_table("email_challenges")
    op.drop_column("users", "two_factor_enabled")
