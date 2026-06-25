"""add learning ladder

Revision ID: 20260624_0009
Revises: 20260624_0008
Create Date: 2026-06-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "20260624_0009"
down_revision: str | None = "20260624_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ladder_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("goal_track", sa.String(length=40), nullable=False),
        sa.Column("current_level", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "goal_track IN ('course', 'lanqiao', 'icpc', 'self_study')",
            name="ck_ladder_templates_goal_track",
        ),
        sa.CheckConstraint(
            "current_level IN ('beginner', 'elementary', 'popularization', 'improvement')",
            name="ck_ladder_templates_current_level",
        ),
        sa.CheckConstraint("version > 0", name="ck_ladder_templates_version"),
        sa.UniqueConstraint("goal_track", "current_level", "version", name="uq_ladder_templates_track_level_version"),
    )
    op.create_index(
        "ix_ladder_templates_track_level_default",
        "ladder_templates",
        ["goal_track", "current_level", "is_default"],
    )
    op.create_index(
        "uq_ladder_templates_default_track_level",
        "ladder_templates",
        ["goal_track", "current_level"],
        unique=True,
        postgresql_where=sa.text("is_default = true"),
    )

    op.create_table(
        "learning_paths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("goal_track", sa.String(length=40), nullable=False),
        sa.Column("current_level", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["ladder_templates.id"], ondelete="SET NULL"),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_learning_paths_status"),
    )
    op.create_index("ix_learning_paths_user_id", "learning_paths", ["user_id"])
    op.create_index("ix_learning_paths_user_status", "learning_paths", ["user_id", "status"])
    op.create_index(
        "uq_learning_paths_active_user",
        "learning_paths",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
    )

    op.create_table(
        "learning_path_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("path_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("phase_index", sa.Integer(), nullable=False),
        sa.Column("node_index", sa.Integer(), nullable=False),
        sa.Column("algorithm_key", sa.String(length=120), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("material_markdown", sa.Text(), nullable=False),
        sa.Column(
            "resource_links",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "unlock_rule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["path_id"], ["learning_paths.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.CheckConstraint("phase_index > 0", name="ck_learning_path_nodes_phase_index"),
        sa.CheckConstraint("node_index > 0", name="ck_learning_path_nodes_node_index"),
        sa.UniqueConstraint("path_id", "phase_index", "node_index", name="uq_learning_path_nodes_path_phase_node"),
    )
    op.create_index("ix_learning_path_nodes_path_id", "learning_path_nodes", ["path_id"])
    op.create_index("ix_learning_path_nodes_topic_id", "learning_path_nodes", ["topic_id"])

    op.create_table(
        "node_user_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("material_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("practice_completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("exam_passed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("material_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("practice_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exam_passed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["node_id"], ["learning_path_nodes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "node_id", name="uq_node_user_progress_user_node"),
    )
    op.create_index("ix_node_user_progress_user_id", "node_user_progress", ["user_id"])
    op.create_index("ix_node_user_progress_node_id", "node_user_progress", ["node_id"])


def downgrade() -> None:
    op.drop_index("ix_node_user_progress_node_id", table_name="node_user_progress")
    op.drop_index("ix_node_user_progress_user_id", table_name="node_user_progress")
    op.drop_table("node_user_progress")

    op.drop_index("ix_learning_path_nodes_topic_id", table_name="learning_path_nodes")
    op.drop_index("ix_learning_path_nodes_path_id", table_name="learning_path_nodes")
    op.drop_table("learning_path_nodes")

    op.drop_index("uq_learning_paths_active_user", table_name="learning_paths")
    op.drop_index("ix_learning_paths_user_status", table_name="learning_paths")
    op.drop_index("ix_learning_paths_user_id", table_name="learning_paths")
    op.drop_table("learning_paths")

    op.drop_index("uq_ladder_templates_default_track_level", table_name="ladder_templates")
    op.drop_index("ix_ladder_templates_track_level_default", table_name="ladder_templates")
    op.drop_table("ladder_templates")
