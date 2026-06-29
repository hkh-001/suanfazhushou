import json
from time import sleep

import httpx

from app.providers.ai.base import AIProvider, AIProviderError, AIProviderResult, AIProviderUsage
from app.core.config import settings
from app.services.settings.ai_runtime_settings import EffectiveAISettings, get_effective_ai_settings


class OpenAICompatibleProvider(AIProvider):
    provider_name = "openai_compatible"

    def __init__(self, effective_settings: EffectiveAISettings | None = None) -> None:
        self.effective_settings = effective_settings

    def _get_config(self) -> EffectiveAISettings:
        effective_settings = self.effective_settings or get_effective_ai_settings()
        if not effective_settings.configured:
            raise AIProviderError(
                "AI_CONFIG_MISSING",
                "AI provider configuration is missing",
                status_code=503,
            )
        return effective_settings

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        ai_settings = self._get_config()
        url = f"{ai_settings.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": ai_settings.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are AlgoMentor AI, an educational algorithm tutor.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2 if prompt_type == "problem_generation" else 0.4,
        }
        headers = {
            "Authorization": f"Bearer {ai_settings.api_key}",
            "Content-Type": "application/json",
        }
        attempts = max(settings.ai_max_retries, 0) + 1
        last_error: AIProviderError | None = None
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=settings.ai_timeout_seconds) as client:
                    response = client.post(url, json=payload, headers=headers)
                if 400 <= response.status_code < 500:
                    raise AIProviderError("AI_PROVIDER_ERROR", "AI provider rejected the request")
                if response.status_code >= 500:
                    last_error = AIProviderError("AI_PROVIDER_ERROR", "AI provider returned an error")
                    if attempt < attempts - 1:
                        sleep(2**attempt)
                        continue
                    raise last_error
                data = response.json()
                content = str(data["choices"][0]["message"]["content"])
                usage = data.get("usage", {})
                return AIProviderResult(
                    content=content,
                    model=str(data.get("model") or ai_settings.model),
                    usage=AIProviderUsage(
                        input_tokens=usage.get("prompt_tokens"),
                        output_tokens=usage.get("completion_tokens"),
                    ),
                )
            except httpx.TimeoutException as exc:
                last_error = AIProviderError("AI_PROVIDER_TIMEOUT", "AI provider request timed out", status_code=503)
                if attempt < attempts - 1:
                    sleep(2**attempt)
                    continue
                raise last_error from exc
            except httpx.ConnectError as exc:
                last_error = AIProviderError("AI_PROVIDER_ERROR", "AI provider connection failed")
                if attempt < attempts - 1:
                    sleep(2**attempt)
                    continue
                raise last_error from exc
            except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
                raise AIProviderError("AI_PROVIDER_ERROR", "AI provider returned an invalid response") from exc
        raise last_error or AIProviderError("AI_PROVIDER_ERROR", "AI provider request failed")
