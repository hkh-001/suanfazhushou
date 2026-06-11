"""add problem display ids

Revision ID: 20260611_0004
Revises: 20260610_0003
Create Date: 2026-06-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260611_0004"
down_revision: str | None = "20260610_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("problems", sa.Column("display_id", sa.Integer(), nullable=True))
    op.execute(
        """
        WITH numbered AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY created_by_user_id
                    ORDER BY created_at, id
                ) AS display_id
            FROM problems
        )
        UPDATE problems
        SET display_id = numbered.display_id
        FROM numbered
        WHERE problems.id = numbered.id
        """
    )
    op.alter_column("problems", "display_id", nullable=False)
    op.create_unique_constraint(
        "uq_problems_user_display_id",
        "problems",
        ["created_by_user_id", "display_id"],
    )

    op.create_table(
        "user_problem_counters",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("next_display_id", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.execute(
        """
        INSERT INTO user_problem_counters (user_id, next_display_id, updated_at)
        SELECT created_by_user_id, max(display_id) + 1, now()
        FROM problems
        GROUP BY created_by_user_id
        """
    )


def downgrade() -> None:
    op.drop_table("user_problem_counters")
    op.drop_constraint("uq_problems_user_display_id", "problems", type_="unique")
    op.drop_column("problems", "display_id")
