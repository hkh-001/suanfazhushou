from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.deps import get_optional_current_user
from app.core.security import clear_session_cookie, create_access_token, set_session_cookie
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import AuthLoginRequest, AuthRegisterRequest, AuthUser, LogoutResult
from app.schemas.common import DataResponse
from app.services.auth import authenticate_user, register_user, to_auth_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=DataResponse[AuthUser])
def register(
    payload: AuthRegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> DataResponse[AuthUser]:
    user = register_user(
        db,
        student_id=payload.student_id,
        password=payload.password,
        name=payload.name,
        current_level=payload.current_level,
        goal_track=payload.goal_track,
        goal_description=payload.goal_description,
    )
    set_session_cookie(response, create_access_token(user.id))
    return DataResponse(data=to_auth_user(user))


@router.post("/login", response_model=DataResponse[AuthUser])
def login(
    payload: AuthLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> DataResponse[AuthUser]:
    user = authenticate_user(db, student_id=payload.student_id, password=payload.password)
    set_session_cookie(response, create_access_token(user.id))
    return DataResponse(data=to_auth_user(user))


@router.post("/logout", response_model=DataResponse[LogoutResult])
def logout(response: Response) -> DataResponse[LogoutResult]:
    clear_session_cookie(response)
    return DataResponse(data=LogoutResult(success=True))


@router.get("/me", response_model=DataResponse[AuthUser])
def me(current_user: User | None = Depends(get_optional_current_user)) -> DataResponse[AuthUser]:
    if current_user is None:
        # get_optional_current_user returns None only when auth is required but absent.
        # The branch is kept explicit for response model clarity.
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTH_REQUIRED", "message": "Authentication is required"},
        )

    return DataResponse(data=to_auth_user(current_user, is_dev_user=current_user.hashed_password is None))
