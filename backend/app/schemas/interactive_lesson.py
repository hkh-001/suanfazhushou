from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


InteractiveLessonStatus = Literal["pending", "submitted", "processing", "completed", "failed"]


class InteractiveLessonDetail(BaseModel):
    id: UUID
    topic_id: UUID
    provider: Literal["openmaic"]
    status: InteractiveLessonStatus
    title: str
    classroom_url: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
