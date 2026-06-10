from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
    learning_stage: str = "beginner",
    target_track: str = "algorithm_basics",
) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        learning_stage=learning_stage,
        target_track=target_track,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
