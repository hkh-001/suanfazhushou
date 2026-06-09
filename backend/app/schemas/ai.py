from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


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


class GeneratedProblem(BaseModel):
    title: str
    statement: str
    input_format: str
    output_format: str
    constraints: str
    sample_input: str
    sample_output: str
    hints: list[str]
    solution_idea: str
    is_ai_generated: Literal[True]
