from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class TestCaseRequest(BaseModel):
    id: UUID
    case_index: int = Field(gt=0)
    name: str | None = None
    input_text: str
    expected_output_text: str
    is_sample: bool


class JudgeRequest(BaseModel):
    submission_id: UUID
    language: Literal["cpp", "python"]
    source_code: str = Field(min_length=1, max_length=20000)
    test_cases: list[TestCaseRequest] = Field(min_length=1, max_length=100)


class CaseResult(BaseModel):
    test_case_id: UUID
    case_index: int
    name: str | None = None
    is_sample: bool
    verdict: Literal[
        "accepted",
        "wrong_answer",
        "runtime_error",
        "time_limit_exceeded",
        "memory_limit_exceeded",
        "output_limit_exceeded",
        "not_run",
    ]
    execution_time_ms: int | None = None
    memory_kb: int | None = None
    actual_output: str | None = None
    error_message: str | None = None


class JudgeResponse(BaseModel):
    verdict: Literal[
        "accepted",
        "wrong_answer",
        "compile_error",
        "runtime_error",
        "time_limit_exceeded",
        "memory_limit_exceeded",
        "output_limit_exceeded",
        "internal_error",
    ]
    passed_case_count: int
    total_case_count: int
    execution_time_ms: int | None = None
    memory_kb: int | None = None
    compile_output: str | None = None
    error_message: str | None = None
    case_results: list[CaseResult] = Field(default_factory=list)
