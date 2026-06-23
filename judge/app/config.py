from pydantic_settings import BaseSettings, SettingsConfigDict


class JudgeSettings(BaseSettings):
    judge_internal_token: str = ""
    judge_max_concurrent: int = 2
    judge_compile_timeout_seconds: int = 10
    judge_case_timeout_seconds: int = 2
    judge_total_timeout_seconds: int = 30
    judge_request_hard_timeout_seconds: int = 50
    judge_memory_limit_mb: int = 512
    judge_cpu_limit: float = 1
    judge_container_pids_limit: int = 128
    judge_runtime_process_limit: int = 64
    judge_workspace_limit_mb: int = 64
    judge_output_limit_bytes: int = 65536
    judge_runner_image: str = "algomentor-judge-runner:phase10"
    judge_stale_container_seconds: int = 300

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = JudgeSettings()
