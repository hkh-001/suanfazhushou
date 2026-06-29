from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user_ai_setting import UserAISetting


def get_user_ai_setting(db: Session, *, user_id: UUID) -> UserAISetting | None:
    return db.scalar(select(UserAISetting).where(UserAISetting.user_id == user_id))


def get_active_user_ai_setting(db: Session, *, user_id: UUID) -> UserAISetting | None:
    return db.scalar(
        select(UserAISetting).where(
            UserAISetting.user_id == user_id,
            UserAISetting.is_active.is_(True),
        )
    )


def upsert_user_ai_setting(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    base_url: str,
    api_key: str,
    model: str,
) -> UserAISetting:
    setting = get_user_ai_setting(db, user_id=user_id)
    if setting is None:
        setting = UserAISetting(
            user_id=user_id,
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            is_active=True,
        )
        db.add(setting)
    else:
        setting.provider = provider
        setting.base_url = base_url
        setting.api_key = api_key
        setting.model = model
        setting.is_active = True
    db.commit()
    db.refresh(setting)
    return setting


def delete_user_ai_setting(db: Session, *, user_id: UUID) -> None:
    setting = get_user_ai_setting(db, user_id=user_id)
    if setting is None:
        return
    db.delete(setting)
    db.commit()
