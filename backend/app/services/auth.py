from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.users import create_user, get_user_by_email, get_user_by_id, get_user_by_username
from app.schemas.auth import AuthUser


def to_auth_user(user: User, *, is_dev_user: bool = False) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        username=user.username,
        learning_stage=user.learning_stage,
        target_track=user.target_track,
        is_dev_user=is_dev_user,
    )


def get_dev_user(db: Session) -> User:
    user = get_user_by_id(db, UUID(settings.dev_user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DEV_USER_NOT_FOUND",
                "message": "Development user not found. Run uv run python scripts/seed_topics.py first.",
            },
        )
    return user


def register_user(db: Session, *, email: str, username: str, password: str) -> User:
    if get_user_by_email(db, email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EMAIL_ALREADY_REGISTERED", "message": "Email is already registered"},
        )
    if get_user_by_username(db, username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "USERNAME_ALREADY_TAKEN", "message": "Username is already taken"},
        )

    return create_user(
        db,
        email=email,
        username=username,
        hashed_password=hash_password(password),
        learning_stage="beginner",
        target_track="algorithm_basics",
    )


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )
    return user
