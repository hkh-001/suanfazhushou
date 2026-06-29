from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.providers.ai.base import AIProviderError
from app.providers.ai.openai_compatible import OpenAICompatibleProvider
from app.schemas.settings import AISettingsResponse, AISettingsTestResponse, AISettingsUpdateRequest
from app.services.settings.ai_runtime_settings import (
    persistent_settings_enabled,
)
from app.services.settings.user_ai_settings import (
    clear_user_ai_settings,
    get_effective_ai_settings_for_user,
    set_user_ai_settings,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _status_response(db: Session, user: User) -> AISettingsResponse:
    effective = get_effective_ai_settings_for_user(db, user)
    return AISettingsResponse(
        data={
            "configured": effective.configured,
            "source": effective.source,
            "provider": effective.provider,
            "base_url": effective.base_url,
            "model": effective.model,
            "api_key_set": effective.api_key_set,
            "runtime_settings_enabled": settings.enable_runtime_ai_settings,
            "persistent_settings_enabled": persistent_settings_enabled(),
        }
    )


@router.get("/ai", response_model=AISettingsResponse)
def get_ai_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    return _status_response(db, current_user)


@router.put("/ai", response_model=AISettingsResponse)
def update_ai_settings(
    payload: AISettingsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    set_user_ai_settings(
        db,
        user=current_user,
        base_url=payload.base_url,
        api_key=payload.api_key,
        model=payload.model,
    )
    return _status_response(db, current_user)


@router.delete("/ai", response_model=AISettingsResponse)
def delete_ai_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    clear_user_ai_settings(db, user=current_user)
    return _status_response(db, current_user)


@router.post("/ai/test", response_model=AISettingsTestResponse)
def test_ai_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsTestResponse:
    effective = get_effective_ai_settings_for_user(db, current_user)
    try:
        OpenAICompatibleProvider(effective).complete(
            prompt='Reply with "ok" only.',
            prompt_type="settings_test",
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    return AISettingsTestResponse(data={"ok": True})
