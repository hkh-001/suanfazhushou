from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.ai import AIUsage
from app.schemas.ladder import LadderSummary


LadderExamQuestionType = Literal["single_choice", "code_reading"]
LadderExamAttemptStatus = Literal["generated", "submitted"]


class LadderExamOption(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    text: str = Field(min_length=1, max_length=500)

    @field_validator("id", "text")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class LadderExamQuestion(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    type: LadderExamQuestionType
    prompt: str = Field(min_length=1, max_length=1500)
    options: list[LadderExamOption] = Field(min_length=4, max_length=4)
    correct_option_id: str = Field(min_length=1, max_length=40)
    explanation: str = Field(min_length=1, max_length=1000)

    @field_validator("id", "prompt", "correct_option_id", "explanation")
    @classmethod
    def strip_question_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_correct_option(self) -> "LadderExamQuestion":
        option_ids = [option.id for option in self.options]
        if len(option_ids) != len(set(option_ids)):
            raise ValueError("Option ids must be unique")
        if self.correct_option_id not in option_ids:
            raise ValueError("Correct option id must match an option")
        return self


class LadderExamPayload(BaseModel):
    questions: list[LadderExamQuestion] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def validate_question_mix(self) -> "LadderExamPayload":
        ids = [question.id for question in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("Question ids must be unique")
        single_count = sum(1 for question in self.questions if question.type == "single_choice")
        code_count = sum(1 for question in self.questions if question.type == "code_reading")
        if single_count != 10 or code_count != 2:
            raise ValueError("Exam must contain 10 single_choice and 2 code_reading questions")
        return self


class LadderExamPublicQuestion(BaseModel):
    id: str
    type: LadderExamQuestionType
    prompt: str
    options: list[LadderExamOption]
    explanation: str | None = None
    correct_option_id: str | None = None


class LadderExamAnswer(BaseModel):
    question_id: str = Field(min_length=1, max_length=80)
    option_id: str = Field(min_length=1, max_length=40)

    @field_validator("question_id", "option_id")
    @classmethod
    def strip_answer_text(cls, value: str) -> str:
        return value.strip()


class LadderExamSubmitRequest(BaseModel):
    answers: list[LadderExamAnswer] = Field(min_length=12, max_length=12)


class LadderExamQuestionResult(BaseModel):
    question_id: str
    selected_option_id: str | None = None
    correct_option_id: str
    correct: bool
    points: int
    explanation: str


class LadderExamAttemptDetail(BaseModel):
    id: UUID
    node_id: UUID
    status: LadderExamAttemptStatus
    questions: list[LadderExamPublicQuestion]
    score: int | None = None
    passed: bool
    submitted_answers: list[LadderExamAnswer] | None = None
    results: list[LadderExamQuestionResult] | None = None
    created_at: datetime
    submitted_at: datetime | None = None


class LadderExamGenerationResult(BaseModel):
    attempt: LadderExamAttemptDetail


class LadderExamSubmitResult(BaseModel):
    attempt: LadderExamAttemptDetail
    score: int
    passed: bool
    ladder: LadderSummary


class LadderExamAIResult(BaseModel):
    payload: LadderExamPayload
    model: str
    usage: AIUsage
