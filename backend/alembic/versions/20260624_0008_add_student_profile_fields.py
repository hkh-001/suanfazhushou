"""add student profile fields

Revision ID: 20260624_0008
Revises: 20260619_0007
Create Date: 2026-06-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "20260624_0008"
down_revision: str | None = "20260619_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CURRENT_LEVELS = ("beginner", "elementary", "popularization", "improvement")
GOAL_TRACKS = ("course", "lanqiao", "icpc", "self_study")


def _map_current_level(value: str | None) -> str:
    if value in CURRENT_LEVELS:
        return value
    if value in {"algorithm_basics", "basic", "beginner"}:
        return "beginner"
    return "beginner"


def _map_goal_track(value: str | None) -> str:
    if value in GOAL_TRACKS:
        return value
    if value in {"algorithm_basics", "beginner", "basic"}:
        return "self_study"
    return "self_study"


def _unique_student_id(base: str, used: set[str]) -> str:
    candidate = base.strip().lower()[:80] or "student"
    if candidate not in used:
        used.add(candidate)
        return candidate
    index = 2
    while True:
        suffix = f"_{index}"
        trimmed = candidate[: 80 - len(suffix)]
        next_candidate = f"{trimmed}{suffix}"
        if next_candidate not in used:
            used.add(next_candidate)
            return next_candidate
        index += 1


def upgrade() -> None:
    op.add_column("users", sa.Column("student_id", sa.String(length=80), nullable=True))
    op.add_column("users", sa.Column("name", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("current_level", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("goal_track", sa.String(length=40), nullable=True))
    op.add_column("users", sa.Column("goal_description", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True))

    bind = op.get_bind()
    users = bind.execute(
        sa.text(
            """
            SELECT id, username, learning_stage, target_track
            FROM users
            ORDER BY created_at, id
            """
        )
    ).mappings()
    used: set[str] = set()
    for user in users:
        user_id = str(user["id"])
        username = (user["username"] or "").strip()
        base_student_id = username or f"legacy_{user_id[:8]}"
        student_id = _unique_student_id(base_student_id, used)
        name = (username or "学生用户")[:40]
        bind.execute(
            sa.text(
                """
                UPDATE users
                SET student_id = :student_id,
                    name = :name,
                    current_level = :current_level,
                    goal_track = :goal_track,
                    onboarding_completed_at = COALESCE(onboarding_completed_at, now())
                WHERE id = :id
                """
            ),
            {
                "id": user["id"],
                "student_id": student_id,
                "name": name,
                "current_level": _map_current_level(user["learning_stage"]),
                "goal_track": _map_goal_track(user["target_track"]),
            },
        )

    op.alter_column("users", "student_id", nullable=False)
    op.alter_column("users", "name", nullable=False)
    op.alter_column("users", "current_level", nullable=False)
    op.alter_column("users", "goal_track", nullable=False)
    op.create_index("ix_users_student_id", "users", ["student_id"], unique=True)
    op.create_check_constraint(
        "ck_users_current_level",
        "users",
        "current_level IN ('beginner', 'elementary', 'popularization', 'improvement')",
    )
    op.create_check_constraint(
        "ck_users_goal_track",
        "users",
        "goal_track IN ('course', 'lanqiao', 'icpc', 'self_study')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_goal_track", "users", type_="check")
    op.drop_constraint("ck_users_current_level", "users", type_="check")
    op.drop_index("ix_users_student_id", table_name="users")
    op.drop_column("users", "onboarding_completed_at")
    op.drop_column("users", "goal_description")
    op.drop_column("users", "goal_track")
    op.drop_column("users", "current_level")
    op.drop_column("users", "name")
    op.drop_column("users", "student_id")
