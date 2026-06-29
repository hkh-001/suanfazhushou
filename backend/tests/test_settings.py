import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.user_ai_setting import UserAISetting
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


def register(client: TestClient, student_id: str) -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "student_id": student_id,
            "password": "password123",
            "name": student_id,
            "current_level": "beginner",
            "goal_track": "self_study",
            "goal_description": "",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def test_get_ai_settings_unconfigured(client: TestClient, dev_user, monkeypatch: pytest.MonkeyPatch) -> None:
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


def test_get_ai_settings_uses_env_fallback_without_exposing_key(
    client: TestClient,
    dev_user,
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
    assert "env-secret-key" not in response.text


def test_put_ai_settings_saves_user_config_without_exposing_key(
    client: TestClient,
    db_session,
    dev_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)

    response = client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://user.example/v1?secret=query#fragment",
            "api_key": "user-key",
            "model": "user-model",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["configured"] is True
    assert body["source"] == "user"
    assert body["base_url"] == "https://user.example/v1"
    assert body["model"] == "user-model"
    assert body["api_key_set"] is True
    assert "user-key" not in response.text
    saved = db_session.query(UserAISetting).one()
    assert saved.api_key == "user-key"


def test_put_ai_settings_validates_base_url(client: TestClient, dev_user) -> None:
    response = client.put(
        "/api/settings/ai",
        json={"base_url": "ftp://provider.example/v1", "api_key": "key", "model": "model"},
    )

    assert response.status_code == 422


def test_user_ai_settings_are_isolated_between_accounts(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    register(client, "settings_a")
    first = client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://a.example/v1",
            "api_key": "key-a",
            "model": "model-a",
        },
    )
    assert first.status_code == 200
    client.post("/api/auth/logout")

    register(client, "settings_b")
    second = client.get("/api/settings/ai")

    assert second.status_code == 200
    body = second.json()["data"]
    assert body["source"] == "none"
    assert body["configured"] is False
    assert "key-a" not in second.text


def test_delete_ai_settings_removes_only_current_user_config_and_falls_back_to_env(
    client: TestClient,
    db_session,
    dev_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "ai_base_url", "https://env.example/v1")
    monkeypatch.setattr(settings, "ai_api_key", "env-key")
    monkeypatch.setattr(settings, "ai_model", "env-model")
    client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://user.example/v1",
            "api_key": "user-key",
            "model": "user-model",
        },
    )
    assert db_session.query(UserAISetting).count() == 1

    response = client.delete("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["source"] == "env"
    assert body["base_url"] == "https://env.example/v1"
    assert body["model"] == "env-model"
    assert body["api_key_set"] is True
    assert db_session.query(UserAISetting).count() == 0
    assert "user-key" not in response.text
    assert "env-key" not in response.text


def test_user_config_survives_runtime_reset(
    client: TestClient,
    dev_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://user.example/v1",
            "api_key": "user-key",
            "model": "user-model",
        },
    )

    from app.services.settings import ai_runtime_settings

    ai_runtime_settings._runtime_ai_settings = None
    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["source"] == "user"
    assert body["configured"] is True
    assert body["base_url"] == "https://user.example/v1"
    assert body["model"] == "user-model"
    assert "user-key" not in response.text


def test_runtime_config_remains_available_as_fallback(
    client: TestClient,
    dev_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    set_runtime_ai_settings(
        base_url="https://runtime.example/v1",
        api_key="runtime-key",
        model="runtime-model",
    )

    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["source"] == "runtime"
    assert body["base_url"] == "https://runtime.example/v1"
    assert "runtime-key" not in response.text


def test_ai_settings_test_uses_current_user_key(
    client: TestClient,
    dev_user,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_env_ai(monkeypatch)
    client.put(
        "/api/settings/ai",
        json={
            "base_url": "https://user.example/v1",
            "api_key": "user-key",
            "model": "user-model",
        },
    )
    FakeClient.calls = 0
    FakeClient.prompts = []
    FakeClient.headers_list = []
    monkeypatch.setattr(httpx, "Client", FakeClient)

    response = client.post("/api/settings/ai/test")

    assert response.status_code == 200
    assert response.json() == {"data": {"ok": True}}
    assert FakeClient.prompts == ['Reply with "ok" only.']
    assert FakeClient.headers_list[0]["Authorization"] == "Bearer user-key"
    assert "user-key" not in response.text


def test_settings_requires_auth_when_dev_user_disabled(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.get("/api/settings/ai")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"
