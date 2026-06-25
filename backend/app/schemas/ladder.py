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


class LadderChoiceOption(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=500)

    @field_validator("id", "text")
    @classmethod
    def strip_option_text(cls, value: str) -> str:
        return value.strip()


class LadderChoicePracticeItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    type: Literal["choice"]
    prompt: str = Field(min_length=1, max_length=1000)
    options: list[LadderChoiceOption] = Field(min_length=2, max_length=8)

    @field_validator("id", "prompt")
    @classmethod
    def strip_choice_text(cls, value: str) -> str:
        return value.strip()


class LadderCodingPracticeItem(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    type: Literal["coding"]
    prompt: str = Field(min_length=1, max_length=1500)
    self_check: str = Field(min_length=1, max_length=1000)

    @field_validator("id", "prompt", "self_check")
    @classmethod
    def strip_coding_text(cls, value: str) -> str:
        return value.strip()


LadderPracticeItem = LadderChoicePracticeItem | LadderCodingPracticeItem


class LadderChoiceAnswer(BaseModel):
    item_id: str = Field(min_length=1, max_length=80)
    option_id: str = Field(min_length=1, max_length=40)

    @field_validator("item_id", "option_id")
    @classmethod
    def strip_answer_text(cls, value: str) -> str:
        return value.strip()


class LadderPracticeSubmitRequest(BaseModel):
    choice_answers: list[LadderChoiceAnswer] = Field(default_factory=list, max_length=100)
    completed_coding_item_ids: list[str] = Field(default_factory=list, max_length=100)

    @field_validator("completed_coding_item_ids")
    @classmethod
    def strip_completed_coding_ids(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class LadderChoiceResult(BaseModel):
    item_id: str
    correct: bool
    explanation: str | None = None


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
    practice_items: list[LadderPracticeItem]
    practice_completed_at: datetime | None = None


class LadderPracticeSubmitResult(BaseModel):
    score: int
    passed: bool
    practice_completed: bool
    choice_results: list[LadderChoiceResult]
    ladder: LadderSummary
