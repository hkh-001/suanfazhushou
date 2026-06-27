"""extend interactive lessons sources

Revision ID: 20260627_0014
Revises: 20260627_0013
Create Date: 2026-06-27 00:14:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260627_0014"
down_revision: Union[str, None] = "20260627_0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "interactive_lessons",
        sa.Column("source_type", sa.String(length=30), server_default="topic", nullable=False),
    )
    op.add_column(
        "interactive_lessons",
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.alter_column("interactive_lessons", "topic_id", existing_type=postgresql.UUID(as_uuid=True), nullable=True)
    op.create_foreign_key(
        "fk_interactive_lessons_node_id_learning_path_nodes",
        "interactive_lessons",
        "learning_path_nodes",
        ["node_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(
        "ix_interactive_lessons_user_node_created",
        "interactive_lessons",
        ["user_id", "node_id", "created_at"],
    )
    op.create_check_constraint(
        "ck_interactive_lessons_source_type",
        "interactive_lessons",
        "source_type IN ('topic','ladder_node')",
    )
    op.create_check_constraint(
        "ck_interactive_lessons_single_source",
        "interactive_lessons",
        "("
        "source_type = 'topic' AND topic_id IS NOT NULL AND node_id IS NULL"
        ") OR ("
        "source_type = 'ladder_node' AND node_id IS NOT NULL AND topic_id IS NULL"
        ")",
    )


def downgrade() -> None:
    # Phase 19B cannot represent ladder-node lessons. This downgrade is intentionally lossy.
    op.execute("DELETE FROM interactive_lessons WHERE source_type = 'ladder_node'")
    op.drop_constraint("ck_interactive_lessons_single_source", "interactive_lessons", type_="check")
    op.drop_constraint("ck_interactive_lessons_source_type", "interactive_lessons", type_="check")
    op.drop_index("ix_interactive_lessons_user_node_created", table_name="interactive_lessons")
    op.drop_constraint("fk_interactive_lessons_node_id_learning_path_nodes", "interactive_lessons", type_="foreignkey")
    op.drop_column("interactive_lessons", "node_id")
    op.drop_column("interactive_lessons", "source_type")
    op.alter_column("interactive_lessons", "topic_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)
