"""add code reviews and mistake notes

Revision ID: 20260612_0005
Revises: 20260611_0004
Create Date: 2026-06-12
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260612_0005"
down_revision: str | None = "20260611_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "code_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("language", sa.String(length=30), nullable=False),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("analysis_result", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=True),
        sa.Column("prompt_type", sa.String(length=80), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("language IN ('cpp', 'python')", name="ck_code_reviews_language"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_code_reviews_user_created_at", "code_reviews", ["user_id", "created_at"])
    op.create_index("ix_code_reviews_user_problem", "code_reviews", ["user_id", "problem_id"])
    op.create_index("ix_code_reviews_user_topic", "code_reviews", ["user_id", "topic_id"])

    op.create_table(
        "mistake_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("code_review_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("error_type", sa.String(length=80), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("wrong_code", sa.Text(), nullable=True),
        sa.Column("fixed_code", sa.Text(), nullable=True),
        sa.Column("fix_suggestion", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("user_reflection", sa.Text(), nullable=True),
        sa.Column("review_status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "review_status IN ('open', 'reviewing', 'resolved')",
            name="ck_mistake_notes_review_status",
        ),
        sa.ForeignKeyConstraint(["code_review_id"], ["code_reviews.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mistake_notes_user_created_at", "mistake_notes", ["user_id", "created_at"])
    op.create_index("ix_mistake_notes_user_problem", "mistake_notes", ["user_id", "problem_id"])
    op.create_index("ix_mistake_notes_user_status", "mistake_notes", ["user_id", "review_status"])
    op.create_index("ix_mistake_notes_user_topic", "mistake_notes", ["user_id", "topic_id"])


def downgrade() -> None:
    op.drop_index("ix_mistake_notes_user_topic", table_name="mistake_notes")
    op.drop_index("ix_mistake_notes_user_status", table_name="mistake_notes")
    op.drop_index("ix_mistake_notes_user_problem", table_name="mistake_notes")
    op.drop_index("ix_mistake_notes_user_created_at", table_name="mistake_notes")
    op.drop_table("mistake_notes")

    op.drop_index("ix_code_reviews_user_topic", table_name="code_reviews")
    op.drop_index("ix_code_reviews_user_problem", table_name="code_reviews")
    op.drop_index("ix_code_reviews_user_created_at", table_name="code_reviews")
    op.drop_table("code_reviews")
