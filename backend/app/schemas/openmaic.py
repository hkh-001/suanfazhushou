from typing import Literal

from pydantic import BaseModel, Field


OpenMAICStatus = Literal["submitted", "pending", "processing", "completed", "failed", "unknown"]
OpenMAICAuthMode = Literal["none", "header", "query", "body"]


class OpenMAICPocStatus(BaseModel):
    enabled: bool
    configured: bool
    base_url: str | None
    generate_path: str
    auth_configured: bool
    auth_mode: str


class OpenMAICPocGenerateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    audience_level: str = Field(min_length=1, max_length=40)
    goal: str | None = Field(default=None, max_length=120)
    summary: str = Field(min_length=1, max_length=1000)


class OpenMAICGeneratePayload(BaseModel):
    requirement: str = Field(min_length=1, max_length=2000)
    language: str = "zh-CN"
    enable_tts: bool = False
    enable_image_generation: bool = False
    enable_video_generation: bool = False
    web_search: bool = False


class OpenMAICJobStatus(BaseModel):
    status: OpenMAICStatus
    job_id: str | None = None
    poll_url: str | None = None
    classroom_url: str | None = None
    message: str | None = None
