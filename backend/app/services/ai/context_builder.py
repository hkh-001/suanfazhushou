from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.topics import get_published_topic


class ContextBuilder:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_topic_context(self, topic_id: UUID | None) -> str:
        if topic_id is None:
            return ""
        topic = get_published_topic(self.db, topic_id)
        if topic is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "TOPIC_NOT_FOUND", "message": "Topic not found"},
            )
        parts = [
            f"Topic title: {topic.title}",
            f"Summary: {topic.summary}",
            f"Content: {topic.content_markdown}",
        ]
        if topic.complexity_note:
            parts.append(f"Complexity note: {topic.complexity_note}")
        if topic.common_pitfalls:
            parts.append(f"Common pitfalls: {topic.common_pitfalls}")
        return "\n\n".join(parts)
