from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.providers.ai.base import AIProviderError
from app.providers.ai.openai_compatible import OpenAICompatibleProvider
from app.schemas.settings import AISettingsResponse, AISettingsTestResponse, AISettingsUpdateRequest
from app.services.settings.ai_runtime_settings import (
    clear_runtime_ai_settings,
    get_effective_ai_settings,
    set_runtime_ai_settings,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _feature_guard() -> None:
    if not settings.enable_runtime_ai_settings:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FEATURE_DISABLED",
                "message": "Runtime AI settings are disabled",
            },
        )


def _status_response() -> AISettingsResponse:
    effective = get_effective_ai_settings()
    return AISettingsResponse(
        data={
            "configured": effective.configured,
            "source": effective.source,
            "provider": effective.provider,
            "base_url": effective.base_url,
            "model": effective.model,
            "api_key_set": effective.api_key_set,
            "runtime_settings_enabled": settings.enable_runtime_ai_settings,
        }
    )


@router.get("/ai", response_model=AISettingsResponse)
def get_ai_settings() -> AISettingsResponse:
    return _status_response()


@router.put("/ai", response_model=AISettingsResponse)
def update_ai_settings(payload: AISettingsUpdateRequest) -> AISettingsResponse:
    _feature_guard()
    set_runtime_ai_settings(
        base_url=payload.base_url,
        api_key=payload.api_key,
        model=payload.model,
    )
    return _status_response()


@router.delete("/ai", response_model=AISettingsResponse)
def delete_ai_settings() -> AISettingsResponse:
    _feature_guard()
    clear_runtime_ai_settings()
    return _status_response()


@router.post("/ai/test", response_model=AISettingsTestResponse)
def test_ai_settings() -> AISettingsTestResponse:
    _feature_guard()
    try:
        OpenAICompatibleProvider().complete(
            prompt='Reply with "ok" only.',
            prompt_type="settings_test",
        )
    except AIProviderError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    return AISettingsTestResponse(data={"ok": True})
