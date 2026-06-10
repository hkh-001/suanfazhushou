from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest
from sqlalchemy import delete

from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, create_access_token
from app.models.user import User


def _payload(email: str | None = None, username: str | None = None, password: str = "password123") -> dict:
    suffix = uuid4().hex[:8]
    return {
        "email": email or f"user-{suffix}@example.com",
        "username": username or f"user_{suffix}",
        "password": password,
    }


def test_register_creates_user_sets_cookie_and_defaults(client, db_session) -> None:
    response = client.post("/api/auth/register", json=_payload())

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["is_dev_user"] is False
    assert body["learning_stage"] == "beginner"
    assert body["target_track"] == "algorithm_basics"
    assert SESSION_COOKIE_NAME in response.cookies

    user = db_session.get(User, body["id"])
    assert user is not None
    assert user.hashed_password is not None
    assert user.hashed_password != "password123"


def test_register_duplicate_email_returns_409(client) -> None:
    payload = _payload()
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 200

    duplicate = client.post("/api/auth/register", json={**_payload(), "email": payload["email"]})

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


def test_register_duplicate_username_returns_409(client) -> None:
    payload = _payload()
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 200

    duplicate = client.post("/api/auth/register", json={**_payload(), "username": payload["username"]})

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "USERNAME_ALREADY_TAKEN"


def test_register_short_password_returns_422(client) -> None:
    response = client.post("/api/auth/register", json=_payload(password="short"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_login_sets_cookie_and_me_returns_real_user(client) -> None:
    payload = _payload()
    client.post("/api/auth/register", json=payload)
    client.cookies.clear()

    login = client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    assert SESSION_COOKIE_NAME in login.cookies

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    body = me.json()["data"]
    assert body["email"] == payload["email"]
    assert body["username"] == payload["username"]
    assert body["is_dev_user"] is False


@pytest.mark.parametrize(
    ("email", "password"),
    [("missing@example.com", "password123"), ("user@example.com", "wrong-password")],
)
def test_login_invalid_credentials_returns_same_error(client, email, password) -> None:
    if email == "user@example.com":
        client.post("/api/auth/register", json=_payload(email=email))

    response = client.post("/api/auth/login", json={"email": email, "password": password})

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
