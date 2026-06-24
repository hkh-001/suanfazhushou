from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.settings.ai_runtime_settings import sanitize_base_url


class AISettingsStatus(BaseModel):
    configured: bool
    source: Literal["runtime", "persistent", "env", "none"]
    provider: str
    base_url: str | None
    model: str | None
    api_key_set: bool
    runtime_settings_enabled: bool
    persistent_settings_enabled: bool


class AISettingsResponse(BaseModel):
    data: AISettingsStatus


class AISettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    base_url: str = Field(min_length=1)
    api_key: str = Field(min_length=1)
    model: str = Field(min_length=1)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        return sanitize_base_url(value)

    @field_validator("api_key", "model")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("field is required")
        return value.strip()


class AISettingsTestResponse(BaseModel):
    data: dict[str, bool]
