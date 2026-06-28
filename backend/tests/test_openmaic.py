from uuid import uuid4

import httpx
import pytest

from app.api import openmaic as openmaic_api
from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, create_access_token
from app.schemas.openmaic import OpenMAICJobStatus


class FakeOpenMAICClient:
    generated_payloads = []
    requested_jobs = []

    async def generate_classroom(self, payload):
        FakeOpenMAICClient.generated_payloads.append(payload)
        return OpenMAICJobStatus(
            status="submitted",
            job_id="job-123",
            poll_url="/api/generate-classroom/job-123",
            classroom_url=None,
            message="accepted",
        )

    async def get_job(self, job_id: str):
        FakeOpenMAICClient.requested_jobs.append(job_id)
        return OpenMAICJobStatus(
            status="completed",
            job_id=job_id,
            poll_url=None,
            classroom_url="http://openmaic.local/classroom/job-123",
            message=None,
        )


class FakeAsyncClient:
    responses: list[httpx.Response | Exception] = []
    requests: list[dict] = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def request(self, method, url, *, headers, json):
        FakeAsyncClient.requests.append(
            {"method": method, "url": url, "headers": headers, "json": json, "timeout": self.timeout}
        )
        item = FakeAsyncClient.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        item.request = httpx.Request(method, url)
        return item


def _login_as(client, user) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, create_access_token(user.id))


def _openmaic_payload(**overrides) -> dict:
    payload = {
        "title": "双指针入门",
        "audience_level": "入门",
        "goal": "蓝桥杯基础训练",
        "summary": "讲解左右指针、快慢指针和常见边界错误。",
    }
    payload.update(overrides)
    return payload


def _enable_openmaic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "enable_openmaic_integration", True)
    monkeypatch.setattr(settings, "openmaic_base_url", "http://openmaic.local")
    monkeypatch.setattr(settings, "openmaic_generate_path", "/api/generate-classroom")
    monkeypatch.setattr(settings, "openmaic_poll_path_template", "/api/generate-classroom/{job_id}")
    monkeypatch.setattr(settings, "openmaic_request_timeout_seconds", 30)
    monkeypatch.setattr(settings, "openmaic_auth_mode", "none")
    monkeypatch.setattr(settings, "openmaic_auth_header_name", "")
    monkeypatch.setattr(settings, "openmaic_auth_header_value", "")
    monkeypatch.setattr(settings, "openmaic_auth_query_name", "")
    monkeypatch.setattr(settings, "openmaic_auth_query_value", "")
    monkeypatch.setattr(settings, "openmaic_auth_body_field", "")
    monkeypatch.setattr(settings, "openmaic_auth_body_value", "")


def test_openmaic_generate_feature_disabled_returns_feature_disabled(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    monkeypatch.setattr(settings, "enable_openmaic_integration", False)
    monkeypatch.setattr(settings, "openmaic_base_url", "")

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FEATURE_DISABLED"


def test_openmaic_requires_admin_role(client, monkeypatch) -> None:
    _enable_openmaic(monkeypatch)
    client.post(
        "/api/auth/register",
        json={
            "student_id": f"user_{uuid4().hex[:8]}",
            "password": "password123",
            "name": "普通用户",
            "current_level": "beginner",
            "goal_track": "self_study",
            "goal_description": None,
        },
    )

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ADMIN_REQUIRED"


def test_openmaic_status_for_admin_hides_auth_value(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    monkeypatch.setattr(settings, "openmaic_base_url", "http://openmaic.local/app?secret=x#hash")
    monkeypatch.setattr(settings, "openmaic_auth_mode", "header")
    monkeypatch.setattr(settings, "openmaic_auth_header_name", "X-OpenMAIC-Code")
    monkeypatch.setattr(settings, "openmaic_auth_header_value", "secret-code")

    response = client.get("/api/openmaic/poc/status")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "enabled": True,
        "configured": True,
        "base_url": "http://openmaic.local/app",
        "generate_path": "/api/generate-classroom",
        "auth_configured": True,
        "auth_mode": "header",
    }
    assert "secret-code" not in response.text


def test_openmaic_generate_with_fake_client_uses_safe_requirement(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeOpenMAICClient.generated_payloads = []
    monkeypatch.setattr(openmaic_api, "get_openmaic_client", lambda: FakeOpenMAICClient())

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 200
    assert response.json()["data"]["job_id"] == "job-123"
    payload = FakeOpenMAICClient.generated_payloads[0]
    assert payload.language == "zh-CN"
    assert payload.enable_tts is False
    assert payload.enable_image_generation is False
    assert payload.enable_video_generation is False
    assert payload.web_search is False
    assert "双指针入门" in payload.requirement
    assert "学号" not in payload.requirement
    assert "correct_option_id" not in payload.requirement
    assert "exam_payload" not in payload.requirement


def test_openmaic_job_lookup_uses_fake_client_once(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeOpenMAICClient.requested_jobs = []
    monkeypatch.setattr(openmaic_api, "get_openmaic_client", lambda: FakeOpenMAICClient())

    response = client.get("/api/openmaic/poc/jobs/job-123")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
    assert FakeOpenMAICClient.requested_jobs == ["job-123"]


def test_openmaic_missing_base_url_returns_config_missing(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    monkeypatch.setattr(settings, "openmaic_base_url", "")

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OPENMAIC_CONFIG_MISSING"


@pytest.mark.parametrize(
    ("auth_mode", "expected_location"),
    [
        ("none", "none"),
        ("header", "header"),
        ("query", "query"),
        ("body", "body"),
    ],
)
def test_openmaic_adapter_auth_modes(client, admin_user, monkeypatch, auth_mode, expected_location) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [
        httpx.Response(202, json={"jobId": "job-123", "pollUrl": "/poll/job-123", "status": "pending"})
    ]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(settings, "openmaic_auth_mode", auth_mode)
    monkeypatch.setattr(settings, "openmaic_auth_header_name", "X-OpenMAIC-Code")
    monkeypatch.setattr(settings, "openmaic_auth_header_value", "secret-code")
    monkeypatch.setattr(settings, "openmaic_auth_query_name", "access_code")
    monkeypatch.setattr(settings, "openmaic_auth_query_value", "secret-code")
    monkeypatch.setattr(settings, "openmaic_auth_body_field", "accessCode")
    monkeypatch.setattr(settings, "openmaic_auth_body_value", "secret-code")

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 200
    request = FakeAsyncClient.requests[0]
    assert request["json"]["language"] == "zh-CN"
    assert request["json"]["enableTTS"] is False
    assert request["json"]["enableImageGeneration"] is False
    assert request["json"]["enableVideoGeneration"] is False
    assert request["json"]["webSearch"] is False
    if expected_location == "none":
        assert "secret-code" not in str(request)
    if expected_location == "header":
        assert request["headers"]["X-OpenMAIC-Code"] == "secret-code"
    if expected_location == "query":
        assert "access_code=secret-code" in request["url"]
    if expected_location == "body":
        assert request["json"]["accessCode"] == "secret-code"
    assert "secret-code" not in response.text


def test_openmaic_adapter_timeout_maps_to_safe_error(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [httpx.TimeoutException("slow")]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "OPENMAIC_TIMEOUT"


def test_openmaic_adapter_connection_error_maps_to_safe_error(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [httpx.ConnectError("down")]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OPENMAIC_UNAVAILABLE"


@pytest.mark.parametrize("status_code", [401, 403])
def test_openmaic_adapter_auth_failure_maps_to_safe_error(client, admin_user, monkeypatch, status_code) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [httpx.Response(status_code)]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OPENMAIC_AUTH_FAILED"


def test_openmaic_adapter_invalid_response_maps_to_safe_error(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [httpx.Response(200, content=b"not-json")]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "OPENMAIC_INVALID_RESPONSE"


def test_openmaic_adapter_job_not_found_maps_to_safe_error(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [httpx.Response(404)]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/api/openmaic/poc/jobs/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OPENMAIC_JOB_NOT_FOUND"


def test_openmaic_generate_404_maps_to_unavailable_not_job_not_found(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [httpx.Response(404)]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "OPENMAIC_UNAVAILABLE"


def test_openmaic_poll_path_template_is_used(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    monkeypatch.setattr(settings, "openmaic_poll_path_template", "/jobs/{job_id}/status")
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [
        httpx.Response(200, json={"data": {"id": "job-123", "status": "completed", "url": "http://openmaic/job-123"}})
    ]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/api/openmaic/poc/jobs/job-123")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
    assert FakeAsyncClient.requests[0]["method"] == "GET"
    assert FakeAsyncClient.requests[0]["url"] == "http://openmaic.local/jobs/job-123/status"


def test_openmaic_nested_unknown_status_does_not_override_top_level_completed(
    client,
    admin_user,
    monkeypatch,
) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [
        httpx.Response(
            200,
            json={
                "id": "job-123",
                "status": "finished",
                "lessonUrl": "http://openmaic.local/lesson/job-123",
                "data": {"status": "mystery"},
            },
        )
    ]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    response = client.get("/api/openmaic/poc/jobs/job-123")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["classroom_url"] == "http://openmaic.local/lesson/job-123"


def test_openmaic_adapter_accepts_additional_status_and_url_aliases(client, admin_user, monkeypatch) -> None:
    _login_as(client, admin_user)
    _enable_openmaic(monkeypatch)
    FakeAsyncClient.requests = []
    FakeAsyncClient.responses = [
        httpx.Response(202, json={"id": "job-created", "state": "created"}),
        httpx.Response(
            200,
            json={"result": {"id": "job-created", "state": "building", "outputUrl": "http://openmaic.local/out"}},
        ),
    ]
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    generate_response = client.post("/api/openmaic/poc/generate", json=_openmaic_payload())
    poll_response = client.get("/api/openmaic/poc/jobs/job-created")

    assert generate_response.status_code == 200
    assert generate_response.json()["data"]["status"] == "submitted"
    assert poll_response.status_code == 200
    assert poll_response.json()["data"]["status"] == "processing"
    assert poll_response.json()["data"]["classroom_url"] == "http://openmaic.local/out"
