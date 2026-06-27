"""add interactive lessons

Revision ID: 20260627_0013
Revises: 20260627_0012
Create Date: 2026-06-27 00:13:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260627_0013"
down_revision: Union[str, None] = "20260627_0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interactive_lessons",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), server_default="openmaic", nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("openmaic_job_id", sa.String(length=160), nullable=True),
        sa.Column("openmaic_poll_url", sa.Text(), nullable=True),
        sa.Column("openmaic_classroom_url", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending','submitted','processing','completed','failed')",
            name="ck_interactive_lessons_status",
        ),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_interactive_lessons_user_topic_created",
        "interactive_lessons",
        ["user_id", "topic_id", "created_at"],
    )
    op.create_index("ix_interactive_lessons_user_status", "interactive_lessons", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_interactive_lessons_user_status", table_name="interactive_lessons")
    op.drop_index("ix_interactive_lessons_user_topic_created", table_name="interactive_lessons")
    op.drop_table("interactive_lessons")
