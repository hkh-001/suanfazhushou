from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.problem import ProblemDetail

ImportProblemDifficulty = Literal["beginner", "basic", "intermediate", "advanced"]


def _strip_or_none(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class ZipProblemMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, min_length=1, max_length=180)
    difficulty: ImportProblemDifficulty = "beginner"
    estimated_minutes: int | None = Field(default=None, gt=0)
    source_url: str | None = Field(default=None, max_length=500)
    topic_ids: list[UUID] = Field(default_factory=list)
    sample_case_names: list[str] | None = Field(default=None, max_length=20)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field is required")
        return stripped

    @field_validator("slug", "source_url")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        return _strip_or_none(value)

    @field_validator("sample_case_names")
    @classmethod
    def strip_sample_case_names(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        stripped = [item.strip() for item in value if item.strip()]
        return stripped or None


class ImportedTestCase(BaseModel):
    case_index: int
    name: str
    input_text: str
    expected_output_text: str
    is_sample: bool


class ProblemImportResult(BaseModel):
    problem: ProblemDetail
    test_cases_count: int
