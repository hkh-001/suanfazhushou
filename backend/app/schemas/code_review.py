from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class CodeReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: UUID | None = None
    problem_id: UUID | None = None
    language: Literal["cpp", "python"]
    question: str | None = Field(default=None, max_length=1000)
    code: str = Field(min_length=1, max_length=20000)
    analysis_result: str = Field(min_length=1, max_length=20000)
    model: str | None = Field(default=None, max_length=120)
    prompt_type: str | None = Field(default=None, max_length=80)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)

    @field_validator("code", "analysis_result")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator("question", "model", "prompt_type")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class CodeReviewProblemRef(BaseModel):
    id: UUID
    display_id: int
    title: str


class CodeReviewTopicRef(BaseModel):
    id: UUID
    title: str
    slug: str
    category: str


class CodeReviewListItem(BaseModel):
    id: UUID
    topic_id: UUID | None = None
    problem_id: UUID | None = None
    language: str
    question: str | None = None
    analysis_result: str
    model: str | None = None
    prompt_type: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    topic: CodeReviewTopicRef | None = None
    problem: CodeReviewProblemRef | None = None
    created_at: datetime
    updated_at: datetime


class CodeReviewDetail(CodeReviewListItem):
    code: str


class CodeReviewDeleteResult(BaseModel):
    success: bool
