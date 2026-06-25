from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

ProblemDifficulty = Literal["beginner", "basic", "intermediate", "advanced"]
GeneratedProblemDifficulty = Literal["beginner", "basic", "intermediate"]


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ProblemTopicTag(BaseModel):
    id: UUID
    title: str
    slug: str
    category: str


class ProblemBasePayload(BaseModel):
    source: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=500)
    difficulty: ProblemDifficulty = "beginner"
    estimated_minutes: int | None = Field(default=None, gt=0)
    input_format: str | None = Field(default=None, max_length=5000)
    output_format: str | None = Field(default=None, max_length=5000)
    constraints: str | None = Field(default=None, max_length=5000)
    sample_input: str | None = Field(default=None, max_length=5000)
    sample_output: str | None = Field(default=None, max_length=5000)
    hint: str | None = Field(default=None, max_length=5000)
    solution_markdown: str | None = Field(default=None, max_length=20000)
    solution_code_cpp: str | None = Field(default=None, max_length=20000)
    solution_code_python: str | None = Field(default=None, max_length=20000)
    topic_ids: list[UUID] = Field(default_factory=list)
    is_public: bool = False

    @field_validator(
        "source",
        "source_url",
        "input_format",
        "output_format",
        "constraints",
        "sample_input",
        "sample_output",
        "hint",
        "solution_markdown",
        "solution_code_cpp",
        "solution_code_python",
    )
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class ProblemCreate(ProblemBasePayload):
    title: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, min_length=1, max_length=180)
    description_markdown: str = Field(min_length=1, max_length=20000)

    @field_validator("title", "description_markdown")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator("slug")
    @classmethod
    def strip_slug(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class ProblemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    slug: str | None = Field(default=None, min_length=1, max_length=180)
    source: str | None = Field(default=None, max_length=80)
    source_url: str | None = Field(default=None, max_length=500)
    difficulty: ProblemDifficulty | None = None
    estimated_minutes: int | None = Field(default=None, gt=0)
    description_markdown: str | None = Field(default=None, min_length=1, max_length=20000)
    input_format: str | None = Field(default=None, max_length=5000)
    output_format: str | None = Field(default=None, max_length=5000)
    constraints: str | None = Field(default=None, max_length=5000)
    sample_input: str | None = Field(default=None, max_length=5000)
    sample_output: str | None = Field(default=None, max_length=5000)
    hint: str | None = Field(default=None, max_length=5000)
    solution_markdown: str | None = Field(default=None, max_length=20000)
    solution_code_cpp: str | None = Field(default=None, max_length=20000)
    solution_code_python: str | None = Field(default=None, max_length=20000)
    topic_ids: list[UUID] | None = None
    is_public: bool | None = None

    @field_validator("title", "slug", "description_markdown")
    @classmethod
    def strip_required_update_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator(
        "source",
        "source_url",
        "input_format",
        "output_format",
        "constraints",
        "sample_input",
        "sample_output",
        "hint",
        "solution_markdown",
        "solution_code_cpp",
        "solution_code_python",
    )
    @classmethod
    def strip_optional_update_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)


class GeneratedProblemSaveTestCase(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    input: str = Field(min_length=1, max_length=20000)
    expected_output: str = Field(min_length=1, max_length=20000)
    is_sample: bool = False

    @field_validator("name")
    @classmethod
    def strip_test_case_name(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @field_validator("input", "expected_output")
    @classmethod
    def strip_test_case_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped


class GeneratedProblemSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic_id: UUID | None = None
    difficulty: GeneratedProblemDifficulty
    title: str = Field(min_length=1, max_length=160)
    statement: str = Field(min_length=1, max_length=20000)
    input_format: str = Field(min_length=1, max_length=5000)
    output_format: str = Field(min_length=1, max_length=5000)
    constraints: str | None = Field(default=None, max_length=5000)
    sample_input: str | None = Field(default=None, max_length=5000)
    sample_output: str | None = Field(default=None, max_length=5000)
    test_cases: list[GeneratedProblemSaveTestCase] = Field(min_length=1, max_length=20)
    hints: list[str] = Field(default_factory=list, max_length=10)
    solution_idea: str | None = Field(default=None, max_length=20000)
    requirements: str | None = Field(default=None, max_length=1500)

    @field_validator("title", "statement", "input_format", "output_format")
    @classmethod
    def strip_generated_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator(
        "constraints",
        "sample_input",
        "sample_output",
        "solution_idea",
        "requirements",
    )
    @classmethod
    def strip_generated_optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @field_validator("hints")
    @classmethod
    def strip_hints(cls, value: list[str]) -> list[str]:
        return [hint.strip() for hint in value if hint.strip()]


class ProblemListItem(BaseModel):
    id: UUID
    display_id: int
    title: str
    slug: str
    source: str | None = None
    source_url: str | None = None
    difficulty: str
    estimated_minutes: int | None = None
    is_ai_generated: bool
    is_published: bool
    is_public: bool
    can_edit: bool
    can_delete: bool
    created_by_user_id: UUID
    topic_tags: list[ProblemTopicTag]
    created_at: datetime
    updated_at: datetime


class ProblemDetail(ProblemListItem):
    description_markdown: str
    input_format: str | None = None
    output_format: str | None = None
    constraints: str | None = None
    sample_input: str | None = None
    sample_output: str | None = None
    hint: str | None = None
    solution_markdown: str | None = None
    solution_code_cpp: str | None = None
    solution_code_python: str | None = None
    published_at: datetime | None = None


class ProblemDeleteResult(BaseModel):
    success: bool


class ProblemModelData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_id: int
    title: str
    slug: str
    source: str | None = None
    source_url: str | None = None
    difficulty: str
    estimated_minutes: int | None = None
    description_markdown: str
    input_format: str | None = None
    output_format: str | None = None
    constraints: str | None = None
    sample_input: str | None = None
    sample_output: str | None = None
    hint: str | None = None
    solution_markdown: str | None = None
    solution_code_cpp: str | None = None
    solution_code_python: str | None = None
    is_ai_generated: bool
    is_published: bool
    is_public: bool
    created_by_user_id: UUID
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
