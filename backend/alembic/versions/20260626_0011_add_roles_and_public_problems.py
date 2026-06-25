"""add roles and public problems

Revision ID: 20260626_0011
Revises: 20260625_0010
Create Date: 2026-06-26 00:11:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260626_0011"
down_revision: Union[str, None] = "20260625_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), server_default="user", nullable=False),
    )
    op.create_check_constraint("ck_users_role", "users", "role IN ('user','admin')")

    op.add_column(
        "problems",
        sa.Column("is_public", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.create_index("ix_problems_public_created_at", "problems", ["is_public", "created_at"])
    op.create_index(
        "ix_problems_user_public_created_at",
        "problems",
        ["created_by_user_id", "is_public", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_problems_user_public_created_at", table_name="problems")
    op.drop_index("ix_problems_public_created_at", table_name="problems")
    op.drop_column("problems", "is_public")

    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")
