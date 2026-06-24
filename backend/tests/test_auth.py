from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, create_access_token
from app.models.user import User
from app.services import auth as auth_service


def _payload(
    student_id: str | None = None,
    password: str = "password123",
    name: str = "测试学生",
    current_level: str = "elementary",
    goal_track: str = "lanqiao",
) -> dict:
    suffix = uuid4().hex[:8]
    return {
        "student_id": student_id or f"student_{suffix}",
        "password": password,
        "name": name,
        "current_level": current_level,
        "goal_track": goal_track,
        "goal_description": "希望系统训练算法基础。",
    }


def test_register_creates_user_sets_cookie_and_defaults(client, db_session) -> None:
    response = client.post("/api/auth/register", json=_payload())

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["is_dev_user"] is False
    assert body["student_id"]
    assert body["name"] == "测试学生"
    assert body["current_level"] == "elementary"
    assert body["goal_track"] == "lanqiao"
    assert body["goal_description"] == "希望系统训练算法基础。"
    assert body["learning_stage"] == "elementary"
    assert body["target_track"] == "lanqiao"
    assert SESSION_COOKIE_NAME in response.cookies

    user = db_session.get(User, body["id"])
    assert user is not None
    assert user.student_id == body["student_id"]
    assert user.hashed_password is not None
    assert user.hashed_password != "password123"
    assert user.onboarding_completed_at is not None


def test_register_duplicate_student_id_returns_409(client) -> None:
    payload = _payload()
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 200

    duplicate = client.post("/api/auth/register", json={**_payload(), "student_id": payload["student_id"]})

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "STUDENT_ID_ALREADY_EXISTS"


def test_register_student_id_strip_then_too_short_returns_422(client) -> None:
    response = client.post("/api/auth/register", json=_payload(student_id=" a "))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_duplicate_student_id_is_case_insensitive(client) -> None:
    first = client.post("/api/auth/register", json=_payload(student_id="Student_CASE_001"))
    assert first.status_code == 200
    assert first.json()["data"]["student_id"] == "student_case_001"

    duplicate = client.post("/api/auth/register", json=_payload(student_id="student_case_001"))

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "STUDENT_ID_ALREADY_EXISTS"


def test_register_integrity_conflict_returns_409(client, monkeypatch) -> None:
    def raise_duplicate(*args, **kwargs):
        raise IntegrityError(
            "insert users",
            {},
            Exception("duplicate key value violates unique constraint ix_users_student_id"),
        )

    monkeypatch.setattr(auth_service, "create_user", raise_duplicate)

    response = client.post("/api/auth/register", json=_payload())

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "STUDENT_ID_ALREADY_EXISTS"


def test_register_invalid_profile_returns_422(client) -> None:
    current_level = client.post("/api/auth/register", json=_payload(current_level="expert"))
    goal_track = client.post("/api/auth/register", json=_payload(goal_track="gold-medal"))

    assert current_level.status_code == 422
    assert current_level.json()["error"]["code"] == "VALIDATION_ERROR"
    assert goal_track.status_code == 422
    assert goal_track.json()["error"]["code"] == "VALIDATION_ERROR"


def test_register_short_password_returns_422(client) -> None:
    response = client.post("/api/auth/register", json=_payload(password="short"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_sets_cookie_and_me_returns_real_user(client) -> None:
    payload = _payload()
    client.post("/api/auth/register", json=payload)
    client.cookies.clear()

    login = client.post("/api/auth/login", json={"student_id": payload["student_id"], "password": payload["password"]})
    assert login.status_code == 200
    assert SESSION_COOKIE_NAME in login.cookies

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    body = me.json()["data"]
    assert body["student_id"] == payload["student_id"]
    assert body["name"] == payload["name"]
    assert body["current_level"] == payload["current_level"]
    assert body["goal_track"] == payload["goal_track"]
    assert body["is_dev_user"] is False


def test_login_student_id_is_case_insensitive(client) -> None:
    payload = _payload(student_id="Student_Login_001")
    register = client.post("/api/auth/register", json=payload)
    assert register.status_code == 200
    client.cookies.clear()

    login = client.post("/api/auth/login", json={"student_id": "STUDENT_LOGIN_001", "password": payload["password"]})

    assert login.status_code == 200
    assert login.json()["data"]["student_id"] == "student_login_001"


@pytest.mark.parametrize(
    ("student_id", "password"),
    [("missing_student", "password123"), ("known_student", "wrong-password")],
)
def test_login_invalid_credentials_returns_same_error(client, student_id, password) -> None:
    if student_id == "known_student":
        client.post("/api/auth/register", json=_payload(student_id=student_id))

    response = client.post("/api/auth/login", json={"student_id": student_id, "password": password})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_me_falls_back_to_dev_user_only_when_cookie_missing(client, dev_user) -> None:
    client.cookies.clear()

    response = client.get("/api/auth/me")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["id"] == str(dev_user.id)
    assert body["is_dev_user"] is True


def test_me_without_cookie_and_dev_user_disabled_returns_401(client, monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_logout_clears_cookie_and_does_not_disable_dev_fallback(client, dev_user) -> None:
    payload = _payload()
    client.post("/api/auth/register", json=payload)
    assert SESSION_COOKIE_NAME in client.cookies

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200
    assert logout.json() == {"data": {"success": True}}

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["data"]["id"] == str(dev_user.id)
    assert me.json()["data"]["is_dev_user"] is True


def test_logout_then_me_without_dev_user_returns_401(client, monkeypatch) -> None:
    payload = _payload()
    client.post("/api/auth/register", json=payload)
    monkeypatch.setattr(settings, "enable_dev_user", False)

    logout = client.post("/api/auth/logout")
    assert logout.status_code == 200

    me = client.get("/api/auth/me")
    assert me.status_code == 401
    assert me.json()["error"]["code"] == "AUTH_REQUIRED"


def test_get_current_user_prefers_cookie_user_over_dev_fallback(client, dev_user, published_topic) -> None:
    payload = _payload()
    client.post("/api/auth/register", json=payload)

    response = client.post(
        "/api/learning/records",
        json={
            "topic_id": str(published_topic.id),
            "status": "learning",
            "progress_percent": 50,
            "mastery_level": 2,
            "note": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] != str(dev_user.id)


def test_invalid_token_does_not_fallback_to_dev_user(client, dev_user) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, "not-a-valid-token")

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_INVALID"


def test_expired_token_does_not_fallback_to_dev_user(client, dev_user) -> None:
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(dev_user.id),
            "type": "access",
            "iat": int((now - timedelta(hours=2)).timestamp()),
            "exp": int((now - timedelta(hours=1)).timestamp()),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "TOKEN_EXPIRED"


def test_valid_token_for_missing_user_returns_invalid_session(client, db_session) -> None:
    missing_user_id = uuid4()
    db_session.execute(delete(User).where(User.id == missing_user_id))
    db_session.commit()
    client.cookies.set(SESSION_COOKIE_NAME, create_access_token(missing_user_id))

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_SESSION"


def test_health_does_not_require_auth(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.get("/api/health")

    assert response.status_code == 200
