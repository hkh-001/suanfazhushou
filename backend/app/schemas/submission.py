from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.judge import CaseVerdict, SubmissionVerdict


class SubmissionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    problem_id: UUID
    language: Literal["cpp", "python"]
    source_code: str = Field(min_length=1, max_length=20000)

    @field_validator("source_code")
    @classmethod
    def validate_source_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Source code is required")
        return value


class SubmissionProblemRef(BaseModel):
    id: UUID | None
    display_id: int
    title: str


class SubmissionCaseResultDetail(BaseModel):
    case_index: int
    name: str | None = None
    is_sample: bool
    verdict: CaseVerdict
    execution_time_ms: int | None = None
    memory_kb: int | None = None
    input_text: str | None = None
    expected_output_text: str | None = None
    actual_output: str | None = None
    error_message: str | None = None


class SubmissionDetail(BaseModel):
    id: UUID
    problem: SubmissionProblemRef
    language: str
    source_code: str
    verdict: SubmissionVerdict
    passed_case_count: int
    total_case_count: int
    execution_time_ms: int | None = None
    memory_kb: int | None = None
    compile_output: str | None = None
    error_message: str | None = None
    case_results: list[SubmissionCaseResultDetail]
    created_at: datetime
    finished_at: datetime
