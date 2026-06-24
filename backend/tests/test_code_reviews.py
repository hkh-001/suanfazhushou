from uuid import uuid4

from app.core.config import settings
from app.models.problem import Problem
from app.models.topic import Topic


def _user_payload(prefix: str = "code-review-user") -> dict:
    suffix = uuid4().hex[:8]
    return {
        "student_id": f"{prefix}_{suffix}",
        "password": "password123",
        "name": "代码诊断用户",
        "current_level": "elementary",
        "goal_track": "self_study",
        "goal_description": None,
    }


def _register(client, payload: dict | None = None) -> dict:
    response = client.post("/api/auth/register", json=payload or _user_payload())
    assert response.status_code == 200
    return response.json()["data"]


def _problem_payload(**overrides) -> dict:
    payload = {
        "title": "Code Review Linked Problem",
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
        "language": "cpp",
        "question": "Why is this wrong?",
        "code": "int main(){return 0;}",
        "analysis_result": "The code compiles but does not solve the task.",
        "model": "test-model",
        "prompt_type": "code_review",
        "input_tokens": 10,
        "output_tokens": 20,
    }
    payload.update(overrides)
    return payload


def _create_code_review(client, **overrides) -> dict:
    response = client.post("/api/code-reviews", json=_code_review_payload(**overrides))
    assert response.status_code == 200
    return response.json()["data"]


def test_create_code_review_success_and_owner(client) -> None:
    user = _register(client)

    review = _create_code_review(client)

    assert review["language"] == "cpp"
    assert review["code"] == "int main(){return 0;}"
    assert review["analysis_result"] == "The code compiles but does not solve the task."
    assert review["model"] == "test-model"
    assert review["input_tokens"] == 10
    assert review["output_tokens"] == 20
    assert user["id"]


def test_create_code_review_without_login_returns_auth_required(client, monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.post("/api/code-reviews", json=_code_review_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_code_review_rejects_invalid_fields(client) -> None:
    _register(client)

    language = client.post("/api/code-reviews", json=_code_review_payload(language="java"))
    code = client.post("/api/code-reviews", json=_code_review_payload(code="   "))
    analysis = client.post("/api/code-reviews", json=_code_review_payload(analysis_result=""))

    for response in (language, code, analysis):
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_code_review_topic_must_be_published(client, db_session) -> None:
    _register(client)
    unpublished = Topic(
        title="Draft review topic",
        slug=f"draft-review-{uuid4().hex}",
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

    missing = client.post("/api/code-reviews", json=_code_review_payload(topic_id=str(uuid4())))
    draft = client.post("/api/code-reviews", json=_code_review_payload(topic_id=str(unpublished.id)))

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TOPIC_NOT_FOUND"
    assert draft.status_code == 404
    assert draft.json()["error"]["code"] == "TOPIC_NOT_FOUND"


def test_code_review_can_link_published_topic_and_own_problem(client, published_topic) -> None:
    _register(client)
    problem = _create_problem(client)

    review = _create_code_review(client, topic_id=str(published_topic.id), problem_id=problem["id"])

    assert review["topic"]["id"] == str(published_topic.id)
    assert review["problem"]["id"] == problem["id"]


def test_code_review_rejects_other_user_problem(client) -> None:
    _register(client, _user_payload("owner-a"))
    problem = _create_problem(client)
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))

    response = client.post("/api/code-reviews", json=_code_review_payload(problem_id=problem["id"]))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"


def test_code_review_list_and_detail_are_user_scoped(client) -> None:
    _register(client, _user_payload("owner-a"))
    first = _create_code_review(client, question="Owner A")
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))
    second = _create_code_review(client, question="Owner B")

    listing = client.get("/api/code-reviews")
    other_detail = client.get(f"/api/code-reviews/{first['id']}")
    own_detail = client.get(f"/api/code-reviews/{second['id']}")

    assert listing.status_code == 200
    assert listing.json()["pagination"]["total"] == 1
    assert listing.json()["data"][0]["id"] == second["id"]
    assert other_detail.status_code == 404
    assert other_detail.json()["error"]["code"] == "CODE_REVIEW_NOT_FOUND"
    assert own_detail.status_code == 200
    assert own_detail.json()["data"]["id"] == second["id"]


def test_delete_code_review_is_user_scoped(client) -> None:
    _register(client, _user_payload("owner-a"))
    review = _create_code_review(client)
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))

    other_delete = client.delete(f"/api/code-reviews/{review['id']}")
    client.cookies.clear()
    _register(client, _user_payload("owner-c"))
    own = _create_code_review(client)
    own_delete = client.delete(f"/api/code-reviews/{own['id']}")
    fetched = client.get(f"/api/code-reviews/{own['id']}")

    assert other_delete.status_code == 404
    assert other_delete.json()["error"]["code"] == "CODE_REVIEW_NOT_FOUND"
    assert own_delete.status_code == 200
    assert own_delete.json() == {"data": {"success": True}}
    assert fetched.status_code == 404


def test_deleting_problem_sets_code_review_problem_null(client, db_session) -> None:
    _register(client)
    problem = _create_problem(client)
    review = _create_code_review(client, problem_id=problem["id"])

    db_session.delete(db_session.get(Problem, problem["id"]))
    db_session.commit()
    fetched = client.get(f"/api/code-reviews/{review['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["data"]["problem_id"] is None
    assert fetched.json()["data"]["problem"] is None
