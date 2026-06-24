from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "AlgoMentor AI"
    log_level: str = "INFO"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: str = "postgresql+psycopg://algomentor:algomentor_password@localhost:5432/algomentor?connect_timeout=5"
    enable_dev_user: bool = True
    dev_user_id: str = "00000000-0000-0000-0000-000000000001"
    enable_runtime_ai_settings: bool = False
    enable_persistent_ai_settings: bool = False
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
