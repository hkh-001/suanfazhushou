from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class LearningStatus(BaseModel):
    status: str = "not_started"
    progress_percent: int = 0
    mastery_level: int = 0
    review_count: int = 0
    last_studied_at: datetime | None = None
    next_review_at: datetime | None = None
    note: str | None = None


class TopicListItem(BaseModel):
    id: UUID
    title: str
    slug: str
    category: str
    level: str
    difficulty_score: int
    summary: str
    estimated_minutes: int
    order_index: int
    learning_status: LearningStatus


class TopicDetail(TopicListItem):
    content_markdown: str
    template_code_cpp: str | None = None
    template_code_python: str | None = None
    complexity_note: str | None = None
    common_pitfalls: str | None = None
    published_at: datetime | None = None
