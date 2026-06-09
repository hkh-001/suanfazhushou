import json
from time import sleep

import httpx

from app.core.config import settings
from app.providers.ai.base import AIProvider, AIProviderError, AIProviderResult, AIProviderUsage


class OpenAICompatibleProvider(AIProvider):
    provider_name = "openai_compatible"

    def _validate_config(self) -> None:
        if not settings.ai_base_url or not settings.ai_api_key or not settings.ai_model:
            raise AIProviderError(
                "AI_CONFIG_MISSING",
                "AI provider configuration is missing",
                status_code=503,
            )

    def complete(self, *, prompt: str, prompt_type: str) -> AIProviderResult:
        self._validate_config()
        url = f"{settings.ai_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": settings.ai_model,
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
            "Authorization": f"Bearer {settings.ai_api_key}",
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
                    model=str(data.get("model") or settings.ai_model),
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
