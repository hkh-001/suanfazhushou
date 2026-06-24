from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_student_id,
    get_user_by_username,
)
from app.schemas.auth import AuthUser


def to_auth_user(user: User, *, is_dev_user: bool = False) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        username=user.username,
        student_id=user.student_id,
        name=user.name,
        current_level=user.current_level,
        goal_track=user.goal_track,
        goal_description=user.goal_description,
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


def _unique_internal_username(db: Session, student_id: str) -> str:
    base = f"student_{student_id}"[:80]
    candidate = base
    index = 2
    while get_user_by_username(db, candidate) is not None:
        suffix = f"_{index}"
        candidate = f"{base[: 80 - len(suffix)]}{suffix}"
        index += 1
    return candidate


def _unique_internal_email(db: Session, student_id: str) -> str:
    base_local = student_id.lower().replace("_", "-")[:200]
    candidate = f"{base_local}@students.algomentor.local"
    index = 2
    while get_user_by_email(db, candidate) is not None:
        suffix = f"-{index}"
        candidate = f"{base_local[: 200 - len(suffix)]}{suffix}@students.algomentor.local"
        index += 1
    return candidate


def register_user(
    db: Session,
    *,
    student_id: str,
    password: str,
    name: str,
    current_level: str,
    goal_track: str,
    goal_description: str | None,
) -> User:
    if get_user_by_student_id(db, student_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "STUDENT_ID_ALREADY_EXISTS", "message": "Student id is already registered"},
        )

    try:
        return create_user(
            db,
            email=_unique_internal_email(db, student_id),
            username=_unique_internal_username(db, student_id),
            hashed_password=hash_password(password),
            student_id=student_id,
            name=name,
            current_level=current_level,
            goal_track=goal_track,
            goal_description=goal_description,
            onboarding_completed_at=datetime.now(timezone.utc),
            learning_stage=current_level,
            target_track=goal_track,
        )
    except IntegrityError as exc:
        db.rollback()
        error_text = str(exc.orig).lower()
        if any(field in error_text for field in ("student_id", "email", "username")):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "STUDENT_ID_ALREADY_EXISTS", "message": "Student id is already registered"},
            ) from exc
        raise


def authenticate_user(db: Session, *, student_id: str, password: str) -> User:
    user = get_user_by_student_id(db, student_id)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid student id or password"},
        )
    return user
