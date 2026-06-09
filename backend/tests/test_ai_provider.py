import httpx
import pytest

from app.core.config import settings
from app.providers.ai.base import AIProviderError
from app.providers.ai.openai_compatible import OpenAICompatibleProvider


class FakeClient:
    calls = 0
    responses: list[httpx.Response] = []
    urls: list[str] = []
    payloads: list[dict] = []
    headers_list: list[dict] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url, json, headers):
        FakeClient.calls += 1
        FakeClient.urls.append(url)
        FakeClient.payloads.append(json)
        FakeClient.headers_list.append(headers)
        response = FakeClient.responses.pop(0)
        response.request = httpx.Request("POST", url)
        return response


def configure_ai(monkeypatch: pytest.MonkeyPatch, *, retries: int = 1) -> None:
    monkeypatch.setattr(settings, "ai_base_url", "https://provider.example/v1")
    monkeypatch.setattr(settings, "ai_api_key", "test-key")
    monkeypatch.setattr(settings, "ai_model", "test-model")
    monkeypatch.setattr(settings, "ai_timeout_seconds", 3)
    monkeypatch.setattr(settings, "ai_max_retries", retries)


def reset_fake_client() -> None:
    FakeClient.calls = 0
    FakeClient.urls = []
    FakeClient.payloads = []
    FakeClient.headers_list = []


def test_provider_4xx_does_not_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_ai(monkeypatch, retries=2)
    reset_fake_client()
    FakeClient.responses = [httpx.Response(400, json={"error": "bad request"})]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(AIProviderError) as exc:
        OpenAICompatibleProvider().complete(prompt="hello", prompt_type="concept_explanation")

    assert exc.value.code == "AI_PROVIDER_ERROR"
    assert FakeClient.calls == 1


def test_provider_5xx_retries_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    configure_ai(monkeypatch, retries=1)
    reset_fake_client()
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
    reset_fake_client()
    FakeClient.responses = [httpx.Response(200, content=b"not-json")]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    with pytest.raises(AIProviderError) as exc:
        OpenAICompatibleProvider().complete(prompt="hello", prompt_type="concept_explanation")

    assert exc.value.code == "AI_PROVIDER_ERROR"


def test_provider_prefers_runtime_config_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.settings.ai_runtime_settings import set_runtime_ai_settings

    configure_ai(monkeypatch, retries=0)
    set_runtime_ai_settings(
        base_url="https://runtime.example/v1?secret=query#fragment",
        api_key="runtime-key",
        model="runtime-model",
    )
    reset_fake_client()
    FakeClient.responses = [
        httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "runtime ok"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 4},
            },
        )
    ]
    monkeypatch.setattr(httpx, "Client", FakeClient)

    result = OpenAICompatibleProvider().complete(prompt="hello", prompt_type="concept_explanation")

    assert result.content == "runtime ok"
    assert FakeClient.urls == ["https://runtime.example/v1/chat/completions"]
    assert FakeClient.payloads[0]["model"] == "runtime-model"
    assert FakeClient.headers_list[0]["Authorization"] == "Bearer runtime-key"
