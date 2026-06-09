"""add ai prompt and log tables

Revision ID: 20260609_0002
Revises: 20260609_0001
Create Date: 2026-06-09
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260609_0002"
down_revision: str | None = "20260609_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("type", sa.String(length=80), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("template_key", sa.String(length=120), nullable=False),
        sa.Column("file_path", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("input_schema_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_schema_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_prompt_templates_enabled", "prompt_templates", ["enabled"], unique=False)
    op.create_index("ix_prompt_templates_template_key", "prompt_templates", ["template_key"], unique=False)
    op.create_index("ix_prompt_templates_type", "prompt_templates", ["type"], unique=False)

    op.create_table(
        "ai_call_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("prompt_type", sa.String(length=80), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_call_logs_prompt_type", "ai_call_logs", ["prompt_type"], unique=False)
    op.create_index("ix_ai_call_logs_success", "ai_call_logs", ["success"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_call_logs_success", table_name="ai_call_logs")
    op.drop_index("ix_ai_call_logs_prompt_type", table_name="ai_call_logs")
    op.drop_table("ai_call_logs")
    op.drop_index("ix_prompt_templates_type", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_template_key", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_enabled", table_name="prompt_templates")
    op.drop_table("prompt_templates")
