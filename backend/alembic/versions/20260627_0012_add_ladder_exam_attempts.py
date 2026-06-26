"""add ladder exam attempts

Revision ID: 20260627_0012
Revises: 20260626_0011
Create Date: 2026-06-27 00:12:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260627_0012"
down_revision: Union[str, None] = "20260626_0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ladder_exam_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("exam_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("submitted_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("passed", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("prompt_type", sa.String(length=80), server_default="ladder_exam_generation", nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('generated','submitted')", name="ck_ladder_exam_attempts_status"),
        sa.CheckConstraint("score IS NULL OR (score >= 0 AND score <= 100)", name="ck_ladder_exam_attempts_score"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["path_id"], ["learning_paths.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["node_id"], ["learning_path_nodes.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_ladder_exam_attempts_user_node_created",
        "ladder_exam_attempts",
        ["user_id", "node_id", "created_at"],
    )
    op.create_index("ix_ladder_exam_attempts_user_status", "ladder_exam_attempts", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_ladder_exam_attempts_user_status", table_name="ladder_exam_attempts")
    op.drop_index("ix_ladder_exam_attempts_user_node_created", table_name="ladder_exam_attempts")
    op.drop_table("ladder_exam_attempts")
