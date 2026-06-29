"""add user ai settings

Revision ID: 20260628_0015
Revises: 20260627_0014
Create Date: 2026-06-28 00:15:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260628_0015"
down_revision: Union[str, None] = "20260627_0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_ai_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="openai_compatible"),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_user_ai_settings_user_id"),
    )
    op.create_index("ix_user_ai_settings_user_id", "user_ai_settings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_user_ai_settings_user_id", table_name="user_ai_settings")
    op.drop_table("user_ai_settings")
