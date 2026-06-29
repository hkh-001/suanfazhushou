from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AIUsage(BaseModel):
    input_tokens: int | None = None
    output_tokens: int | None = None


class AIResponseData(BaseModel):
    result: str
    prompt_type: str
    model: str
    usage: AIUsage


class ChatRequest(BaseModel):
    topic_id: UUID | None = None
    question: str = Field(min_length=1, max_length=2000)
    mode: Literal["beginner", "advanced"] = "beginner"


class CodeReviewRequest(BaseModel):
    topic_id: UUID | None = None
    language: Literal["cpp", "python"]
    code: str = Field(min_length=1, max_length=12000)
    question: str | None = Field(default=None, max_length=1000)


class ProblemGenerationRequest(BaseModel):
    topic_id: UUID | None = None
    difficulty: Literal["beginner", "basic", "intermediate"] = "beginner"
    requirements: str | None = Field(default=None, max_length=1500)


class GeneratedProblemTestCase(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    input: str = Field(min_length=1, max_length=20000)
    expected_output: str = Field(min_length=1, max_length=20000)
    is_sample: bool = False


class GeneratedProblem(BaseModel):
    title: str
    statement: str
    input_format: str
    output_format: str
    constraints: str
    sample_input: str
    sample_output: str
    test_cases: list[GeneratedProblemTestCase] = Field(min_length=1, max_length=20)
    hints: list[str]
    solution_idea: str | None = Field(default=None, max_length=20000)
    solution_code_cpp: str | None = Field(default=None, max_length=20000)
    solution_code_python: str | None = Field(default=None, max_length=20000)
    is_ai_generated: Literal[True]

    @model_validator(mode="after")
    def _require_reference_solution(self) -> "GeneratedProblem":
        # The server derives every expected_output by running the reference solution, so a
        # generated problem without any reference solution would silently bypass the Judge
        # self-check. Require at least one language.
        if not (self.solution_code_cpp or self.solution_code_python):
            raise ValueError("at least one of solution_code_cpp or solution_code_python is required")
        return self
