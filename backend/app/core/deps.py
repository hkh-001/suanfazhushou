from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


def get_current_user(db: Session = Depends(get_db)) -> User:
    if not settings.enable_dev_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "AUTH_NOT_CONFIGURED",
                "message": "Authentication is not configured in Phase 2",
            },
        )

    user = db.get(User, UUID(settings.dev_user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DEV_USER_NOT_FOUND",
                "message": "Development user not found. Run uv run python scripts/seed_topics.py first.",
            },
        )
    return user
