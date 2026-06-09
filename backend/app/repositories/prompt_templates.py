from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prompt_template import PromptTemplate


def get_enabled_prompt_template(db: Session, *, template_key: str) -> PromptTemplate | None:
    return db.scalar(
        select(PromptTemplate)
        .where(
            PromptTemplate.template_key == template_key,
            PromptTemplate.enabled.is_(True),
        )
        .order_by(PromptTemplate.version.desc(), PromptTemplate.created_at.desc())
        .limit(1)
    )
