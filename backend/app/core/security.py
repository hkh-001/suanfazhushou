from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, Request, Response, status
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

SESSION_COOKIE_NAME = "algomentor_session"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_SAMESITE = "lax"

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return password_hash.verify(password, hashed_password)


def _is_secure_cookie() -> bool:
    return settings.app_env.lower() == "production"


def create_access_token(user_id: UUID) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=_is_secure_cookie(),
        samesite=SESSION_COOKIE_SAMESITE,
        path=SESSION_COOKIE_PATH,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path=SESSION_COOKIE_PATH,
        httponly=True,
        secure=_is_secure_cookie(),
        samesite=SESSION_COOKIE_SAMESITE,
    )


def get_session_cookie(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)


def decode_access_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_EXPIRED", "message": "Session has expired"},
        ) from exc
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Session token is invalid"},
        ) from exc

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Session token is invalid"},
        )

    subject = payload.get("sub")
    try:
        return UUID(str(subject))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_INVALID", "message": "Session token is invalid"},
        ) from exc
