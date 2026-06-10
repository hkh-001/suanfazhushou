from uuid import UUID

from pydantic import BaseModel, Field, field_validator


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _validate_email(value: str) -> str:
    email = _normalize_email(value)
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("Invalid email")
    local, domain = email.rsplit("@", 1)
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("Invalid email")
    return email


class AuthRegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    username: str = Field(min_length=3, max_length=80)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            raise ValueError("Username is required")
        return username


class AuthLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _validate_email(value)


class AuthUser(BaseModel):
    id: UUID
    email: str
    username: str
    learning_stage: str
    target_track: str
    is_dev_user: bool = False


class LogoutResult(BaseModel):
    success: bool
