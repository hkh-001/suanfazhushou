from dataclasses import dataclass


@dataclass(frozen=True)
class AIProviderUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


@dataclass(frozen=True)
class AIProviderResult:
    content: str
    model: str
    usage: AIProviderUsage


class AIProviderError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class AIProvider:
    provider_name = "unknown"

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        raise NotImplementedError
