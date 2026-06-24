from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


CurrentLevel = Literal["beginner", "elementary", "popularization", "improvement"]
GoalTrack = Literal["course", "lanqiao", "icpc", "self_study"]


class AuthRegisterRequest(BaseModel):
    student_id: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=40)
    current_level: CurrentLevel
    goal_track: GoalTrack
    goal_description: str | None = Field(default=None, max_length=500)

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, value: str) -> str:
        student_id = value.strip().lower()
        if not student_id:
            raise ValueError("Student id is required")
        if len(student_id) < 2:
            raise ValueError("Student id must contain at least 2 characters")
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
        if any(char not in allowed for char in student_id):
            raise ValueError("Student id can only contain letters, numbers, underscores, and hyphens")
        return student_id

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        name = value.strip()
        if len(name) < 2:
            raise ValueError("Name must contain at least 2 characters")
        return name

    @field_validator("goal_description")
    @classmethod
    def validate_goal_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        description = value.strip()
        return description or None


class AuthLoginRequest(BaseModel):
    student_id: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("student_id")
    @classmethod
    def validate_student_id(cls, value: str) -> str:
        student_id = value.strip().lower()
        if len(student_id) < 2:
            raise ValueError("Student id must contain at least 2 characters")
        return student_id


class AuthUser(BaseModel):
    id: UUID
    email: str | None = None
    username: str | None = None
    student_id: str
    name: str
    current_level: str
    goal_track: str
    goal_description: str | None = None
    learning_stage: str
    target_track: str
    is_dev_user: bool = False


class LogoutResult(BaseModel):
    success: bool
