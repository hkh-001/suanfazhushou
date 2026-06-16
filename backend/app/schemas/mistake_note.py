from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.code_review import CodeReviewProblemRef, CodeReviewTopicRef

ReviewStatus = Literal["open", "reviewing", "resolved"]


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class MistakeNoteBase(BaseModel):
    problem_id: UUID | None = None
    topic_id: UUID | None = None
    code_review_id: UUID | None = None
    title: str = Field(min_length=1, max_length=160)
    error_type: str | None = Field(default=None, max_length=80)
    root_cause: str = Field(min_length=1, max_length=20000)
    wrong_code: str | None = Field(default=None, max_length=12000)
    fixed_code: str | None = Field(default=None, max_length=12000)
    fix_suggestion: str | None = Field(default=None, max_length=20000)
    ai_summary: str | None = Field(default=None, max_length=20000)
    user_reflection: str | None = Field(default=None, max_length=20000)
    review_status: ReviewStatus = "open"

    @field_validator("title", "root_cause")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator(
        "error_type",
        "wrong_code",
        "fixed_code",
        "fix_suggestion",
        "ai_summary",
        "user_reflection",
    )
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class MistakeNoteCreate(MistakeNoteBase):
    model_config = ConfigDict(extra="forbid")


class MistakeNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: UUID | None = None
    topic_id: UUID | None = None
    code_review_id: UUID | None = None
    title: str | None = Field(default=None, min_length=1, max_length=160)
    error_type: str | None = Field(default=None, max_length=80)
    root_cause: str | None = Field(default=None, min_length=1, max_length=20000)
    wrong_code: str | None = Field(default=None, max_length=12000)
    fixed_code: str | None = Field(default=None, max_length=12000)
    fix_suggestion: str | None = Field(default=None, max_length=20000)
    ai_summary: str | None = Field(default=None, max_length=20000)
    user_reflection: str | None = Field(default=None, max_length=20000)
    review_status: ReviewStatus | None = None

    @field_validator("title", "root_cause")
    @classmethod
    def strip_required_update_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator(
        "error_type",
        "wrong_code",
        "fixed_code",
        "fix_suggestion",
        "ai_summary",
        "user_reflection",
    )
    @classmethod
    def strip_optional_update_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @model_validator(mode="after")
    def validate_required_fields_when_provided(self) -> "MistakeNoteUpdate":
        for field_name in ("title", "root_cause"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null when provided")
        return self


class MistakeCodeReviewRef(BaseModel):
    id: UUID
    language: str
    question: str | None = None
    created_at: datetime


class MistakeNoteListItem(BaseModel):
    id: UUID
    problem_id: UUID | None = None
    topic_id: UUID | None = None
    code_review_id: UUID | None = None
    title: str
    error_type: str | None = None
    root_cause: str
    review_status: ReviewStatus
    resolved_at: datetime | None = None
    problem: CodeReviewProblemRef | None = None
    topic: CodeReviewTopicRef | None = None
    code_review: MistakeCodeReviewRef | None = None
    created_at: datetime
    updated_at: datetime


class MistakeNoteDetail(MistakeNoteListItem):
    wrong_code: str | None = None
    fixed_code: str | None = None
    fix_suggestion: str | None = None
    ai_summary: str | None = None
    user_reflection: str | None = None


class MistakeNoteDeleteResult(BaseModel):
    success: bool
