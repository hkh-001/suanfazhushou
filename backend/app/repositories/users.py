from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_user_by_student_id(db: Session, student_id: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.student_id) == student_id.lower()))


def create_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
    student_id: str,
    name: str,
    current_level: str,
    goal_track: str,
    goal_description: str | None = None,
    onboarding_completed_at: datetime | None = None,
    role: str = "user",
    learning_stage: str = "beginner",
    target_track: str = "algorithm_basics",
) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        student_id=student_id,
        name=name,
        current_level=current_level,
        goal_track=goal_track,
        goal_description=goal_description,
        onboarding_completed_at=onboarding_completed_at,
        role=role,
        learning_stage=learning_stage,
        target_track=target_track,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
