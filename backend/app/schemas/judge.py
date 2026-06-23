from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

JudgeLanguage = Literal["cpp", "python"]
SubmissionVerdict = Literal[
    "accepted",
    "wrong_answer",
    "compile_error",
    "runtime_error",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "output_limit_exceeded",
    "internal_error",
]
CaseVerdict = Literal[
    "accepted",
    "wrong_answer",
    "runtime_error",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "output_limit_exceeded",
    "not_run",
]


class JudgeTestCaseRequest(BaseModel):
    id: UUID
    case_index: int = Field(gt=0)
    name: str | None = None
    input_text: str
    expected_output_text: str
    is_sample: bool


class JudgeRequest(BaseModel):
    submission_id: UUID
    language: JudgeLanguage
    source_code: str = Field(min_length=1, max_length=20000)
    test_cases: list[JudgeTestCaseRequest] = Field(min_length=1, max_length=100)


class JudgeCaseResult(BaseModel):
    test_case_id: UUID
    case_index: int = Field(gt=0)
    name: str | None = None
    is_sample: bool
    verdict: CaseVerdict
    execution_time_ms: int | None = Field(default=None, ge=0)
    memory_kb: int | None = Field(default=None, ge=0)
    actual_output: str | None = None
    error_message: str | None = Field(default=None, max_length=300)


class JudgeResponse(BaseModel):
    verdict: SubmissionVerdict
    passed_case_count: int = Field(ge=0)
    total_case_count: int = Field(gt=0)
    execution_time_ms: int | None = Field(default=None, ge=0)
    memory_kb: int | None = Field(default=None, ge=0)
    compile_output: str | None = None
    error_message: str | None = Field(default=None, max_length=500)
    case_results: list[JudgeCaseResult] = Field(default_factory=list)
