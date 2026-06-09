import httpx
import pytest

from app.core.config import settings
from app.providers.ai.base import AIProviderError
from app.providers.ai.openai_compatible import OpenAICompatibleProvider


class FakeClient:
    calls = 0
    responses: list[httpx.Response] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url, json, headers):
        FakeClient.calls += 1
        response = FakeClient.responses.pop(0)
        response.request = httpx.Request("POST", url)
        return response


def configure_ai(monkeypatch: pytest.MonkeyPatch, *, retries: int = 1) -> None:
    monkeypatch.setattr(settings, "ai_base_url", "https://provider.example/v1")
    monkeypatch.setattr(settings, "ai_api_key", "test-key")
    monkeypatch.setattr(settings, "ai_model", "test-model")
    monkeypatch.setattr(settings, "ai_timeout_seconds", 3)
    monkeypatch.setattr(settings, "ai_max_retries", retries)


def test_provider_4xx_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_ai(monkeypatch, retries=2)
    FakeClient.calls = 0
    FakeClient.responses = [httpx.Response(400, json={"error": "bad request"})]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(AIProviderError) as exc:
        OpenAICompatibleProvider().complete(prompt="hello", prompt_type="concept_explanation")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert FakeClient.calls == 1


def test_provider_5xx_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_ai(monkeypatch, retries=1)
    FakeClient.calls = 0
    FakeClient.responses = [
        httpx.Response(500, json={"error": "temporary"}),
        httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 2},
            },
        ),
    ]
    monkeypatch.setattr(httpx, "Client", FakeClient)
    monkeypatch.setattr("app.providers.ai.openai_compatible.sleep", lambda _seconds: None)

    result = OpenAICompatibleProvider().complete(prompt="hello", prompt_type="concept_explanation")

    assert result.content == "ok"
    assert result.usage.input_tokens == 1
    assert result.usage.output_tokens == 2
    assert FakeClient.calls == 2


def test_provider_200_invalid_json_returns_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_ai(monkeypatch, retries=0)
    FakeClient.calls = 0
    FakeClient.responses = [httpx.Response(200, content=b"not-json")]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(AIProviderError) as exc:
        OpenAICompatibleProvider().complete(prompt="hello", prompt_type="concept_explanation")

    assert exc.value.code == "AI_PROVIDER_ERROR"
