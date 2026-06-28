from pathlib import Path
from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_root: ClassVar[Path] = Path(__file__).resolve().parents[2]
    app_env: str = "development"
    app_name: str = "AlgoMentor AI"
    log_level: str = "INFO"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "postgresql+psycopg://algomentor:algomentor_password@localhost:5432/algomentor?connect_timeout=5"
    enable_dev_user: bool = False
    dev_user_id: str = "00000000-0000-0000-0000-000000000001"
    dev_admin_password: str = ""
    enable_runtime_ai_settings: bool = True
    enable_persistent_ai_settings: bool = True
    persistent_ai_settings_path: str = ".runtime-ai-settings.json"
    secret_key: str = "change-me-in-production-32-bytes-long!!"
    access_token_expire_minutes: int = 1440
    enable_code_execution: bool = False
    judge_base_url: str = "http://localhost:9000"
    judge_internal_token: str = ""
    judge_request_timeout_seconds: int = 60
    submission_max_in_flight: int = 2
    ai_provider: str = "openai_compatible"
    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_timeout_seconds: int = 60
    ai_max_retries: int = 1
    enable_openmaic_integration: bool = False
    openmaic_base_url: str = ""
    openmaic_generate_path: str = "/api/generate-classroom"
    openmaic_poll_path_template: str = "/api/generate-classroom/{job_id}"
    openmaic_request_timeout_seconds: int = 30
    openmaic_max_poll_minutes: int = 5
    openmaic_auth_mode: str = "none"
    openmaic_auth_header_name: str = ""
    openmaic_auth_header_value: str = ""
    openmaic_auth_query_name: str = ""
    openmaic_auth_query_value: str = ""
    openmaic_auth_body_field: str = ""
    openmaic_auth_body_value: str = ""
    cors_origins_raw: str = Field(
        default="http://localhost:3000",
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]


settings = Settings()
