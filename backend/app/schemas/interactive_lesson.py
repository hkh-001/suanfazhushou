from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


InteractiveLessonStatus = Literal["pending", "submitted", "processing", "completed", "failed"]
InteractiveLessonSourceType = Literal["topic", "ladder_node"]


class InteractiveLessonDetail(BaseModel):
    id: UUID
    source_type: InteractiveLessonSourceType
    topic_id: UUID | None
    node_id: UUID | None
    provider: Literal["openmaic"]
    status: InteractiveLessonStatus
    title: str
    classroom_url: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
