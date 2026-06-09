from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.prompt_templates import get_enabled_prompt_template


class PromptRenderer:
    def __init__(self, db: Session) -> None:
        self.db = db

    def render(self, *, template_key: str, values: dict[str, str]) -> str:
        template = get_enabled_prompt_template(self.db, template_key=template_key)
        if template is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "PROMPT_TEMPLATE_NOT_FOUND",
                    "message": "Prompt template not found. Run uv run python scripts/seed_prompt_templates.py first.",
                },
            )
        content = template.content
        for key, value in values.items():
            content = content.replace("{{" + key + "}}", value)
        return content
