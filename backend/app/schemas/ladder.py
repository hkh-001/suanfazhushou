from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


LadderNodeStatus = Literal["locked", "unlocked", "material_done", "practice_done", "passed"]


class LadderPathSummary(BaseModel):
    id: UUID
    status: str
    goal_track: str
    current_level: str
    template_name: str
    created_at: datetime


class LadderResourceLink(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=500)
    source: str | None = Field(default=None, max_length=80)

    @field_validator("title", "url", "source")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class LadderNodeSummary(BaseModel):
    id: UUID
    topic_id: UUID | None
    phase_index: int
    node_index: int
    algorithm_key: str
    title: str
    summary: str
    status: LadderNodeStatus
    locked: bool
    material_completed: bool
    practice_completed: bool
    exam_passed: bool


class LadderPhase(BaseModel):
    phase_index: int
    title: str
    description: str | None = None
    nodes: list[LadderNodeSummary]


class LadderSummary(BaseModel):
    path: LadderPathSummary
    phases: list[LadderPhase]
    current_node_id: UUID | None


class LadderNodeDetail(LadderNodeSummary):
    path_id: UUID
    material_markdown: str
    resource_links: list[LadderResourceLink]
