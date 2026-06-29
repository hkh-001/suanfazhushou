from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token, get_session_cookie
from app.db.session import get_db
from app.models.user import User
from app.providers.ai.base import AIProvider
from app.providers.ai.openai_compatible import OpenAICompatibleProvider
from app.repositories.users import get_user_by_id
from app.services.auth import get_dev_user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = get_session_cookie(request)
    if token:
        user_id = decode_access_token(token)
        user = get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_SESSION", "message": "Session user no longer exists"},
            )
        return user

    if settings.enable_dev_user:
        return get_dev_user(db)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "AUTH_REQUIRED", "message": "Authentication is required"},
    )


def get_optional_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = get_session_cookie(request)
    if token:
        user_id = decode_access_token(token)
        user = get_user_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "INVALID_SESSION", "message": "Session user no longer exists"},
            )
        return user

    if settings.enable_dev_user:
        return get_dev_user(db)

    return None


def get_ai_provider() -> AIProvider:
    # Legacy helper for non-user-scoped provider tests. User-facing AI calls build
    # providers inside AIService so they can use per-user AI settings.
    return OpenAICompatibleProvider()
