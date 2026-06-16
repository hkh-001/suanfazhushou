from uuid import uuid4

from app.core.config import settings
from app.models.code_review import CodeReview
from app.models.problem import Problem
from app.models.topic import Topic


def _user_payload(prefix: str = "mistake-user") -> dict:
    suffix = uuid4().hex[:8]
    return {
        "email": f"{prefix}-{suffix}@example.com",
        "username": f"{prefix}_{suffix}",
        "password": "password123",
    }


def _register(client, payload: dict | None = None) -> dict:
    response = client.post("/api/auth/register", json=payload or _user_payload())
    assert response.status_code == 200
    return response.json()["data"]


def _problem_payload(**overrides) -> dict:
    payload = {
        "title": "Mistake Linked Problem",
        "difficulty": "beginner",
        "description_markdown": "Find the bug.",
        "topic_ids": [],
    }
    payload.update(overrides)
    return payload


def _create_problem(client, **overrides) -> dict:
    response = client.post("/api/problems", json=_problem_payload(**overrides))
    assert response.status_code == 200
    return response.json()["data"]


def _code_review_payload(**overrides) -> dict:
    payload = {
        "language": "python",
        "question": "Why wrong?",
        "code": "print(1)",
        "analysis_result": "The implementation ignores the input.",
    }
    payload.update(overrides)
    return payload


def _create_code_review(client, **overrides) -> dict:
    response = client.post("/api/code-reviews", json=_code_review_payload(**overrides))
    assert response.status_code == 200
    return response.json()["data"]


def _mistake_payload(**overrides) -> dict:
    payload = {
        "title": "Boundary condition mistake",
        "error_type": "boundary",
        "root_cause": "The loop misses the last candidate.",
        "wrong_code": "while l < r: pass",
        "fixed_code": "while l <= r: pass",
        "fix_suggestion": "Use a consistent interval template.",
        "ai_summary": "Check the interval definition first.",
        "user_reflection": "I mixed left-closed and right-open intervals.",
        "review_status": "open",
    }
    payload.update(overrides)
    return payload


def _create_mistake(client, **overrides) -> dict:
    response = client.post("/api/mistakes", json=_mistake_payload(**overrides))
    assert response.status_code == 200
    return response.json()["data"]


def test_create_mistake_note_success(client) -> None:
    user = _register(client)

    note = _create_mistake(client)

    assert note["title"] == "Boundary condition mistake"
    assert note["root_cause"] == "The loop misses the last candidate."
    assert note["review_status"] == "open"
    assert note["resolved_at"] is None
    assert user["id"]


def test_create_mistake_note_without_login_returns_auth_required(client, monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.post("/api/mistakes", json=_mistake_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_mistake_note_validates_required_fields_and_status(client) -> None:
    _register(client)

    title = client.post("/api/mistakes", json=_mistake_payload(title=" "))
    root_cause = client.post("/api/mistakes", json=_mistake_payload(root_cause=""))
    review_status = client.post("/api/mistakes", json=_mistake_payload(review_status="closed"))

    for response in (title, root_cause, review_status):
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_mistake_note_can_link_topic_problem_and_code_review(client, published_topic) -> None:
    _register(client)
    problem = _create_problem(client)
    review = _create_code_review(client)

    note = _create_mistake(
        client,
        topic_id=str(published_topic.id),
        problem_id=problem["id"],
        code_review_id=review["id"],
    )

    assert note["topic"]["id"] == str(published_topic.id)
    assert note["problem"]["id"] == problem["id"]
    assert note["code_review"]["id"] == review["id"]


def test_mistake_note_rejects_invalid_associations(client, db_session) -> None:
    _register(client, _user_payload("owner-a"))
    other_problem = _create_problem(client)
    other_review = _create_code_review(client)
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))
    unpublished = Topic(
        title="Draft mistake topic",
        slug=f"draft-mistake-{uuid4().hex}",
        category="Draft",
        level="beginner",
        difficulty_score=1,
        summary="Draft",
        content_markdown="Draft",
        estimated_minutes=10,
        status="draft",
        order_index=1,
    )
    db_session.add(unpublished)
    db_session.commit()

    problem = client.post("/api/mistakes", json=_mistake_payload(problem_id=other_problem["id"]))
    review = client.post("/api/mistakes", json=_mistake_payload(code_review_id=other_review["id"]))
    topic = client.post("/api/mistakes", json=_mistake_payload(topic_id=str(unpublished.id)))

    assert problem.status_code == 404
    assert problem.json()["error"]["code"] == "PROBLEM_NOT_FOUND"
    assert review.status_code == 404
    assert review.json()["error"]["code"] == "CODE_REVIEW_NOT_FOUND"
    assert topic.status_code == 404
    assert topic.json()["error"]["code"] == "TOPIC_NOT_FOUND"


def test_mistake_note_list_and_detail_are_user_scoped(client) -> None:
    _register(client, _user_payload("owner-a"))
    first = _create_mistake(client, title="Owner A")
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))
    second = _create_mistake(client, title="Owner B")

    listing = client.get("/api/mistakes")
    filtered = client.get("/api/mistakes?status=open")
    other_detail = client.get(f"/api/mistakes/{first['id']}")
    own_detail = client.get(f"/api/mistakes/{second['id']}")

    assert listing.status_code == 200
    assert listing.json()["pagination"]["total"] == 1
    assert listing.json()["data"][0]["id"] == second["id"]
    assert filtered.status_code == 200
    assert filtered.json()["pagination"]["total"] == 1
    assert other_detail.status_code == 404
    assert other_detail.json()["error"]["code"] == "MISTAKE_NOTE_NOT_FOUND"
    assert own_detail.status_code == 200
    assert own_detail.json()["data"]["id"] == second["id"]


def test_update_mistake_note_and_resolved_at_rules(client) -> None:
    _register(client)
    note = _create_mistake(client)

    resolved = client.put(
        f"/api/mistakes/{note['id']}",
        json={"title": "Updated", "root_cause": "Updated cause", "review_status": "resolved"},
    )
    reopened = client.put(f"/api/mistakes/{note['id']}", json={"review_status": "reviewing"})

    assert resolved.status_code == 200
    assert resolved.json()["data"]["title"] == "Updated"
    assert resolved.json()["data"]["root_cause"] == "Updated cause"
    assert resolved.json()["data"]["review_status"] == "resolved"
    assert resolved.json()["data"]["resolved_at"] is not None
    assert reopened.status_code == 200
    assert reopened.json()["data"]["review_status"] == "reviewing"
    assert reopened.json()["data"]["resolved_at"] is None


def test_update_mistake_note_rejects_other_user_associations(client) -> None:
    _register(client, _user_payload("owner-a"))
    problem = _create_problem(client)
    review = _create_code_review(client)
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))
    note = _create_mistake(client)

    problem_response = client.put(f"/api/mistakes/{note['id']}", json={"problem_id": problem["id"]})
    review_response = client.put(f"/api/mistakes/{note['id']}", json={"code_review_id": review["id"]})

    assert problem_response.status_code == 404
    assert problem_response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"
    assert review_response.status_code == 404
    assert review_response.json()["error"]["code"] == "CODE_REVIEW_NOT_FOUND"


def test_delete_mistake_note_is_user_scoped(client) -> None:
    _register(client, _user_payload("owner-a"))
    note = _create_mistake(client)
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))

    other_delete = client.delete(f"/api/mistakes/{note['id']}")
    own = _create_mistake(client)
    own_delete = client.delete(f"/api/mistakes/{own['id']}")
    fetched = client.get(f"/api/mistakes/{own['id']}")

    assert other_delete.status_code == 404
    assert other_delete.json()["error"]["code"] == "MISTAKE_NOTE_NOT_FOUND"
    assert own_delete.status_code == 200
    assert own_delete.json() == {"data": {"success": True}}
    assert fetched.status_code == 404


def test_deleted_problem_and_code_review_set_mistake_associations_null(client, db_session) -> None:
    _register(client)
    problem = _create_problem(client)
    review = _create_code_review(client)
    note = _create_mistake(client, problem_id=problem["id"], code_review_id=review["id"])

    db_session.delete(db_session.get(Problem, problem["id"]))
    db_session.delete(db_session.get(CodeReview, review["id"]))
    db_session.commit()
    fetched = client.get(f"/api/mistakes/{note['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["data"]["problem_id"] is None
    assert fetched.json()["data"]["problem"] is None
    assert fetched.json()["data"]["code_review_id"] is None
    assert fetched.json()["data"]["code_review"] is None
