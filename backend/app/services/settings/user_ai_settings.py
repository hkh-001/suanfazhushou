from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories.user_ai_settings import (
    delete_user_ai_setting,
    get_active_user_ai_setting,
    upsert_user_ai_setting,
)
from app.services.settings.ai_runtime_settings import (
    EffectiveAISettings,
    get_effective_ai_settings,
    sanitize_base_url,
)


def get_effective_ai_settings_for_user(db: Session, user: User) -> EffectiveAISettings:
    user_setting = get_active_user_ai_setting(db, user_id=user.id)
    if user_setting is not None:
        return EffectiveAISettings(
            provider=user_setting.provider,
            base_url=user_setting.base_url,
            api_key=user_setting.api_key,
            model=user_setting.model,
            source="user",
        )
    return get_effective_ai_settings()


def set_user_ai_settings(
    db: Session,
    *,
    user: User,
    base_url: str,
    api_key: str,
    model: str,
) -> EffectiveAISettings:
    clean_api_key = api_key.strip()
    clean_model = model.strip()
    if not clean_api_key or not clean_model:
        raise ValueError("api_key and model are required")
    setting = upsert_user_ai_setting(
        db,
        user_id=user.id,
        provider=settings.ai_provider,
        base_url=sanitize_base_url(base_url),
        api_key=clean_api_key,
        model=clean_model,
    )
    return EffectiveAISettings(
        provider=setting.provider,
        base_url=setting.base_url,
        api_key=setting.api_key,
        model=setting.model,
        source="user",
    )


def clear_user_ai_settings(db: Session, *, user: User) -> EffectiveAISettings:
    delete_user_ai_setting(db, user_id=user.id)
    return get_effective_ai_settings()
