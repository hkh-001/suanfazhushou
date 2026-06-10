"""add problem bank tables

Revision ID: 20260610_0003
Revises: 20260609_0002
Create Date: 2026-06-10
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260610_0003"
down_revision: str | None = "20260609_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "problems",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("difficulty", sa.String(length=30), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=True),
        sa.Column("description_markdown", sa.Text(), nullable=False),
        sa.Column("input_format", sa.Text(), nullable=True),
        sa.Column("output_format", sa.Text(), nullable=True),
        sa.Column("constraints", sa.Text(), nullable=True),
        sa.Column("sample_input", sa.Text(), nullable=True),
        sa.Column("sample_output", sa.Text(), nullable=True),
        sa.Column("hint", sa.Text(), nullable=True),
        sa.Column("solution_markdown", sa.Text(), nullable=True),
        sa.Column("solution_code_cpp", sa.Text(), nullable=True),
        sa.Column("solution_code_python", sa.Text(), nullable=True),
        sa.Column("is_ai_generated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_published", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "difficulty IN ('beginner', 'basic', 'intermediate', 'advanced')",
            name="ck_problems_difficulty",
        ),
        sa.CheckConstraint("estimated_minutes IS NULL OR estimated_minutes > 0", name="ck_problems_estimated_minutes"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("created_by_user_id", "slug", name="uq_problems_user_slug"),
    )
    op.create_index("ix_problems_created_by_user_id", "problems", ["created_by_user_id"], unique=False)
    op.create_index(
        "ix_problems_user_created_at",
        "problems",
        ["created_by_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_problems_user_difficulty",
        "problems",
        ["created_by_user_id", "difficulty"],
        unique=False,
    )

    op.create_table(
        "problem_tags",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_id", "topic_id", name="uq_problem_tags_problem_topic"),
    )
    op.create_index("ix_problem_tags_problem_id", "problem_tags", ["problem_id"], unique=False)
    op.create_index("ix_problem_tags_topic_id", "problem_tags", ["topic_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_problem_tags_topic_id", table_name="problem_tags")
    op.drop_index("ix_problem_tags_problem_id", table_name="problem_tags")
    op.drop_table("problem_tags")
    op.drop_index("ix_problems_user_difficulty", table_name="problems")
    op.drop_index("ix_problems_user_created_at", table_name="problems")
    op.drop_index("ix_problems_created_by_user_id", table_name="problems")
    op.drop_table("problems")
