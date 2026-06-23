"""add submissions

Revision ID: 20260619_0007
Revises: 20260613_0006
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260619_0007"
down_revision: str | None = "20260613_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("problem_title", sa.String(length=160), nullable=False),
        sa.Column("problem_display_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("verdict", sa.String(length=40), nullable=False),
        sa.Column("passed_case_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_case_count", sa.Integer(), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("compile_output", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("language IN ('cpp', 'python')", name="ck_submissions_language"),
        sa.CheckConstraint(
            "verdict IN ('accepted', 'wrong_answer', 'compile_error', 'runtime_error', "
            "'time_limit_exceeded', 'memory_limit_exceeded', 'output_limit_exceeded', 'internal_error')",
            name="ck_submissions_verdict",
        ),
        sa.CheckConstraint("passed_case_count >= 0", name="ck_submissions_passed_case_count"),
        sa.CheckConstraint("total_case_count > 0", name="ck_submissions_total_case_count"),
        sa.CheckConstraint(
            "passed_case_count <= total_case_count",
            name="ck_submissions_passed_not_above_total",
        ),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_submissions_user_created_at", "submissions", ["user_id", "created_at"])
    op.create_index("ix_submissions_problem_created_at", "submissions", ["problem_id", "created_at"])

    op.create_table(
        "submission_case_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("submission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_case_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("case_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("is_sample", sa.Boolean(), nullable=False),
        sa.Column("verdict", sa.String(length=40), nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("expected_output_text", sa.Text(), nullable=True),
        sa.Column("actual_output", sa.Text(), nullable=True),
        sa.Column("error_message", sa.String(length=300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("case_index > 0", name="ck_submission_case_results_case_index"),
        sa.CheckConstraint(
            "verdict IN ('accepted', 'wrong_answer', 'runtime_error', 'time_limit_exceeded', "
            "'memory_limit_exceeded', 'output_limit_exceeded', 'not_run')",
            name="ck_submission_case_results_verdict",
        ),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "submission_id",
            "case_index",
            name="uq_submission_case_results_submission_case",
        ),
    )
    op.create_index(
        "ix_submission_case_results_submission_id",
        "submission_case_results",
        ["submission_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_submission_case_results_submission_id", table_name="submission_case_results")
    op.drop_table("submission_case_results")
    op.drop_index("ix_submissions_problem_created_at", table_name="submissions")
    op.drop_index("ix_submissions_user_created_at", table_name="submissions")
    op.drop_table("submissions")
