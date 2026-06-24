import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.services.settings.ai_runtime_settings import get_effective_ai_settings, set_runtime_ai_settings


class FakeClient:
    calls = 0
    prompts: list[str] = []
    headers_list: list[dict] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url, json, headers):
        FakeClient.calls += 1
        FakeClient.prompts.append(json["messages"][1]["content"])
        FakeClient.headers_list.append(headers)
        response = httpx.Response(
            200,
            json={
                "model": json["model"],
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
        response.request = httpx.Request("POST", url)
        return response


def clear_env_ai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_base_url", "")
    monkeypatch.setattr(settings, "ai_api_key", "")
    monkeypatch.setattr(settings, "ai_model", "")


def test_get_ai_settings_unconfigured(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    clear_env_ai(monkeypatch)
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", False)
    monkeypatch.setattr(settings, "enable_persistent_ai_settings", False)

    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "configured": False,
        "source": "none",
        "provider": "openai_compatible",
        "base_url": None,
        "model": None,
        "api_key_set": False,
        "runtime_settings_enabled": False,
        "persistent_settings_enabled": False,
    }


def test_get_ai_settings_uses_env_without_exposing_key(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_base_url", "https://env.example/v1?token=secret#hash")
    monkeypatch.setattr(settings, "ai_api_key", "env-secret-key")
    monkeypatch.setattr(settings, "ai_model", "env-model")

    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["configured"] is True
    assert body["source"] == "env"
    assert body["base_url"] == "https://env.example/v1"
    assert body["model"] == "env-model"
    assert body["api_key_set"] is True
    assert body["persistent_settings_enabled"] is False
    assert "env-secret-key" not in response.text


def test_mutating_ai_settings_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", False)

    responses = [
        client.put(
            "/api/settings/ai",
            json={
                "base_url": "https://runtime.example/v1",
                "api_key": "runtime-key",
                "model": "runtime-model",
            },
        ),
        client.delete("/api/settings/ai"),
        client.post("/api/settings/ai/test"),
    ]

    for response in responses:
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "FEATURE_DISABLED"


def test_put_ai_settings_validates_and_sanitizes(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", True)

    invalid = client.put(
        "/api/settings/ai",
        json={"base_url": "ftp://provider.example/v1", "api_key": "key", "model": "model"},
    )
    assert invalid.status_code == 422

    response = client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://runtime.example/v1?secret=query#fragment",
            "api_key": "runtime-key",
            "model": "runtime-model",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["configured"] is True
    assert body["source"] == "runtime"
    assert body["base_url"] == "https://runtime.example/v1"
    assert body["model"] == "runtime-model"
    assert body["api_key_set"] is True
    assert body["persistent_settings_enabled"] is False
    assert "runtime-key" not in response.text


def test_put_ai_settings_can_persist_local_development_config(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    clear_env_ai(monkeypatch)
    settings_path = tmp_path / "ai-settings.json"
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", True)
    monkeypatch.setattr(settings, "enable_persistent_ai_settings", True)
    monkeypatch.setattr(settings, "persistent_ai_settings_path", str(settings_path))

    response = client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://persistent.example/v1?secret=query#fragment",
            "api_key": "persistent-key",
            "model": "persistent-model",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["source"] == "runtime"
    assert body["persistent_settings_enabled"] is True
    assert settings_path.exists()
    assert "persistent-key" not in response.text

    from app.services.settings.ai_runtime_settings import clear_runtime_ai_settings

    clear_runtime_ai_settings()
    assert settings_path.exists() is False


def test_get_ai_settings_uses_persistent_config_after_runtime_reset(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    clear_env_ai(monkeypatch)
    settings_path = tmp_path / "ai-settings.json"
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", True)
    monkeypatch.setattr(settings, "enable_persistent_ai_settings", True)
    monkeypatch.setattr(settings, "persistent_ai_settings_path", str(settings_path))

    client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://persistent.example/v1?secret=query#fragment",
            "api_key": "persistent-key",
            "model": "persistent-model",
        },
    )

    from app.services.settings import ai_runtime_settings

    ai_runtime_settings._runtime_ai_settings = None
    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["configured"] is True
    assert body["source"] == "persistent"
    assert body["base_url"] == "https://persistent.example/v1"
    assert body["model"] == "persistent-model"
    assert body["api_key_set"] is True
    assert body["persistent_settings_enabled"] is True
    assert "persistent-key" not in response.text


def test_invalid_persistent_base_url_is_ignored(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    clear_env_ai(monkeypatch)
    settings_path = tmp_path / "ai-settings.json"
    settings_path.write_text(
        '{"base_url": "file:///tmp/provider", "api_key": "persistent-key", "model": "persistent-model"}',
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", True)
    monkeypatch.setattr(settings, "enable_persistent_ai_settings", True)
    monkeypatch.setattr(settings, "persistent_ai_settings_path", str(settings_path))

    from app.services.settings import ai_runtime_settings

    ai_runtime_settings._runtime_ai_settings = None
    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["configured"] is False
    assert body["source"] == "none"
    assert "persistent-key" not in response.text


def test_delete_ai_settings_clears_runtime_config(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", True)
    set_runtime_ai_settings(
        base_url="https://runtime.example/v1",
        api_key="runtime-key",
        model="runtime-model",
    )

    response = client.delete("/api/settings/ai")

    assert response.status_code == 200
    assert response.json()["data"]["source"] == "none"
    assert get_effective_ai_settings().source == "none"


def test_ai_settings_test_uses_short_prompt_without_exposing_key(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    monkeypatch.setattr(settings, "enable_runtime_ai_settings", True)
    set_runtime_ai_settings(
        base_url="https://runtime.example/v1",
        api_key="runtime-key",
        model="runtime-model",
    )
    FakeClient.calls = 0
    FakeClient.prompts = []
    FakeClient.headers_list = []
    monkeypatch.setattr(httpx, "Client", FakeClient)

    response = client.post("/api/settings/ai/test")

    assert response.status_code == 200
    assert response.json() == {"data": {"ok": True}}
    assert FakeClient.prompts == ['Reply with "ok" only.']
    assert FakeClient.headers_list[0]["Authorization"] == "Bearer runtime-key"
    assert "runtime-key" not in response.text
