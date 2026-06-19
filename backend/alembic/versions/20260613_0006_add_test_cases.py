"""add test cases

Revision ID: 20260613_0006
Revises: 20260612_0005
Create Date: 2026-06-13 00:06:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260613_0006"
down_revision: str | None = "20260612_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "test_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("problem_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("case_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("expected_output_text", sa.Text(), nullable=False),
        sa.Column("is_sample", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_hidden", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("case_index > 0", name="ck_test_cases_case_index_positive"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("problem_id", "case_index", name="uq_test_cases_problem_case_index"),
    )
    op.create_index("ix_test_cases_problem_id", "test_cases", ["problem_id"])
    op.create_index("ix_test_cases_problem_case_index", "test_cases", ["problem_id", "case_index"])


def downgrade() -> None:
    op.drop_index("ix_test_cases_problem_case_index", table_name="test_cases")
    op.drop_index("ix_test_cases_problem_id", table_name="test_cases")
    op.drop_table("test_cases")
