from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

LearningRecordStatus = Literal["not_started", "learning", "mastered"]


class LearningRecordUpsert(BaseModel):
    topic_id: UUID
    status: LearningRecordStatus
    progress_percent: int = Field(ge=0, le=100)
    mastery_level: int = Field(ge=0, le=5)
    note: str | None = None


class LearningRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    topic_id: UUID
    status: str
    progress_percent: int
    mastery_level: int
    review_count: int
    last_studied_at: datetime
    next_review_at: datetime | None = None
    note: str | None = None
