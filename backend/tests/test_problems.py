from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import delete, select, text

from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, create_access_token
from app.models.problem import Problem, UserProblemCounter
from app.models.test_case import TestCase as DbTestCase
from app.models.topic import Topic
from app.models.user import User


def _user_payload(prefix: str = "problem-user") -> dict:
    suffix = uuid4().hex[:8]
    return {
        "student_id": f"{prefix}_{suffix}",
        "password": "password123",
        "name": "题库用户",
        "current_level": "elementary",
        "goal_track": "self_study",
        "goal_description": None,
    }


def _problem_payload(**overrides) -> dict:
    payload = {
        "title": "Two Sum Practice",
        "difficulty": "beginner",
        "estimated_minutes": 25,
        "description_markdown": "Find two numbers with a target sum.",
        "input_format": "An array and a target.",
        "output_format": "Two indices.",
        "constraints": "1 <= n <= 1000",
        "sample_input": "[2,7,11,15], 9",
        "sample_output": "0 1",
        "hint": "Use a hash map.",
        "solution_markdown": "Store seen values while scanning.",
        "solution_code_cpp": "vector<int> solve() { return {}; }",
        "solution_code_python": "def solve():\n    return []",
        "topic_ids": [],
    }
    payload.update(overrides)
    return payload


def _generated_problem_payload(**overrides) -> dict:
    payload = {
        "title": "AI Prefix Sum Practice",
        "difficulty": "basic",
        "statement": "Given an array, answer range sum queries.",
        "input_format": "The first line contains n and q.",
        "output_format": "Print one answer per query.",
        "constraints": "1 <= n, q <= 100000",
        "sample_input": "5 1\n1 2 3 4 5\n1 3",
        "sample_output": "6",
        "test_cases": [
            {
                "name": "01",
                "input": "5 1\n1 2 3 4 5\n1 3",
                "expected_output": "6",
                "is_sample": True,
            },
            {
                "name": "02",
                "input": "5 2\n1 2 3 4 5\n2 4\n1 5",
                "expected_output": "9\n15",
                "is_sample": False,
            },
        ],
        "hints": ["Build prefix sums.", "Use sum[r] - sum[l - 1]."],
        "solution_idea": "Precompute prefix sums to answer each query in O(1).",
    }
    payload.update(overrides)
    return payload


def _register(client, payload: dict | None = None) -> dict:
    user_payload = payload or _user_payload()
    response = client.post("/api/auth/register", json=user_payload)
    assert response.status_code == 200
    return response.json()["data"]


def _login_as(client, user: User) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, create_access_token(user.id))


def _create_problem(client, **overrides) -> dict:
    response = client.post("/api/problems", json=_problem_payload(**overrides))
    assert response.status_code == 200
    return response.json()["data"]


def _save_generated_problem(client, **overrides) -> dict:
    response = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(**overrides))
    assert response.status_code == 200
    return response.json()["data"]


def test_create_problem_success_and_owner(client, db_session) -> None:
    user = _register(client)

    problem = _create_problem(client)

    assert problem["title"] == "Two Sum Practice"
    assert problem["display_id"] == 1
    assert problem["slug"] == "two-sum-practice"
    assert problem["created_by_user_id"] == user["id"]
    assert problem["is_ai_generated"] is False
    assert problem["is_published"] is False

    db_problem = db_session.get(Problem, problem["id"])
    assert db_problem is not None
    assert str(db_problem.created_by_user_id) == user["id"]
    assert db_problem.display_id == 1


def test_user_cannot_create_public_problem(client) -> None:
    _register(client)

    response = client.post("/api/problems", json=_problem_payload(is_public=True))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PUBLIC_PROBLEM_FORBIDDEN"


def test_admin_can_create_and_list_public_problem(client, admin_user) -> None:
    _login_as(client, admin_user)

    created = client.post("/api/problems", json=_problem_payload(is_public=True))
    assert created.status_code == 200
    problem = created.json()["data"]
    assert problem["is_public"] is True
    assert problem["can_edit"] is True

    listed = client.get("/api/problems/public")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [problem["id"]]


def test_public_problem_visible_but_not_editable_to_other_user(client, admin_user) -> None:
    _login_as(client, admin_user)
    problem = client.post("/api/problems", json=_problem_payload(is_public=True)).json()["data"]
    _register(client, _user_payload("public-reader"))

    detail = client.get(f"/api/problems/public/{problem['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["can_edit"] is False

    update = client.put(f"/api/problems/{problem['id']}", json={"title": "Nope"})
    assert update.status_code == 404


def test_public_problem_accessible_via_problem_detail_endpoint_for_any_user(client, admin_user) -> None:
    _login_as(client, admin_user)
    problem = client.post("/api/problems", json=_problem_payload(is_public=True)).json()["data"]
    _register(client, _user_payload("public-detail-reader"))

    response = client.get(f"/api/problems/{problem['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == problem["id"]
    assert response.json()["data"]["is_public"] is True
    assert response.json()["data"]["can_edit"] is False


def test_admin_can_publish_own_private_problem(client, admin_user) -> None:
    _login_as(client, admin_user)
    problem = _create_problem(client)

    response = client.put(f"/api/problems/{problem['id']}", json={"is_public": True})

    assert response.status_code == 200
    assert response.json()["data"]["is_public"] is True


def test_save_ai_generated_problem_success_and_forced_metadata(client, db_session) -> None:
    user = _register(client)

    problem = _save_generated_problem(client)

    assert problem["title"] == "AI Prefix Sum Practice"
    assert problem["display_id"] == 1
    assert problem["created_by_user_id"] == user["id"]
    assert problem["source"] == "ai_generated"
    assert problem["source_url"] is None
    assert problem["is_ai_generated"] is True
    assert problem["is_published"] is False
    assert problem["description_markdown"] == "Given an array, answer range sum queries."
    assert problem["hint"] == "- Build prefix sums.\n- Use sum[r] - sum[l - 1]."
    assert problem["solution_markdown"] == "Precompute prefix sums to answer each query in O(1)."

    db_problem = db_session.get(Problem, problem["id"])
    assert db_problem is not None
    assert str(db_problem.created_by_user_id) == user["id"]
    assert db_problem.is_ai_generated is True
    test_cases = db_session.scalars(
        select(DbTestCase).where(DbTestCase.problem_id == db_problem.id).order_by(DbTestCase.case_index)
    ).all()
    assert len(test_cases) == 2
    assert test_cases[0].name == "01"
    assert test_cases[0].input_text == "5 1\n1 2 3 4 5\n1 3"
    assert test_cases[0].expected_output_text == "6"
    assert test_cases[0].is_sample is True
    assert test_cases[1].is_sample is False


def test_save_ai_generated_problem_rejects_client_owned_fields(client) -> None:
    _register(client)

    response = client.post(
        "/api/problems/save-ai-generated",
        json=_generated_problem_payload(
            user_id=str(uuid4()),
            display_id=99,
            created_by_user_id=str(uuid4()),
            is_ai_generated=False,
            source="manual",
            is_published=True,
        ),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_save_ai_generated_problem_validates_required_fields_and_difficulty(client) -> None:
    _register(client)

    title = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(title="   "))
    statement = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(statement=""))
    input_format = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(input_format=" "))
    output_format = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(output_format=""))
    difficulty = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(difficulty="advanced"))
    test_cases = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(test_cases=[]))

    for response in (title, statement, input_format, output_format, difficulty, test_cases):
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_save_ai_generated_problem_can_associate_published_topic(client, published_topic) -> None:
    _register(client)

    problem = _save_generated_problem(client, topic_id=str(published_topic.id))

    assert len(problem["topic_tags"]) == 1
    assert problem["topic_tags"][0]["id"] == str(published_topic.id)


def test_save_ai_generated_problem_rejects_missing_or_unpublished_topic(client, db_session) -> None:
    _register(client)
    unpublished = Topic(
        title="Draft AI topic",
        slug=f"draft-ai-{uuid4().hex}",
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

    missing = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload(topic_id=str(uuid4())))
    draft = client.post(
        "/api/problems/save-ai-generated",
        json=_generated_problem_payload(topic_id=str(unpublished.id)),
    )

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TOPIC_NOT_FOUND"
    assert draft.status_code == 404
    assert draft.json()["error"]["code"] == "TOPIC_NOT_FOUND"


def test_save_ai_generated_problem_without_login_returns_auth_required(client, monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_save_ai_generated_problem_uses_shared_display_id_sequence(client) -> None:
    _register(client)
    manual = _create_problem(client, title="Manual")
    generated = _save_generated_problem(client, title="Generated")
    after = _create_problem(client, title="Manual After")

    assert manual["display_id"] == 1
    assert generated["display_id"] == 2
    assert after["display_id"] == 3


def test_save_ai_generated_problem_appears_in_list_and_detail(client) -> None:
    _register(client)
    problem = _save_generated_problem(client)

    listed = client.get("/api/problems")
    detail = client.get(f"/api/problems/{problem['id']}")

    assert listed.status_code == 200
    assert listed.json()["data"][0]["id"] == problem["id"]
    assert listed.json()["data"][0]["display_id"] == problem["display_id"]
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == problem["id"]
    assert detail.json()["data"]["is_ai_generated"] is True


def test_save_ai_generated_problem_route_is_not_treated_as_problem_id(client) -> None:
    _register(client)

    response = client.post("/api/problems/save-ai-generated", json=_generated_problem_payload())

    assert response.status_code == 200
    assert response.json()["data"]["title"] == "AI Prefix Sum Practice"


def test_display_id_increments_per_user(client) -> None:
    _register(client)

    first = _create_problem(client, title="First")
    second = _create_problem(client, title="Second")

    assert first["display_id"] == 1
    assert second["display_id"] == 2


def test_display_id_is_independent_per_user(client) -> None:
    _register(client, _user_payload("owner-a"))
    first = _create_problem(client, title="Owner A")
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))

    second = _create_problem(client, title="Owner B")

    assert first["display_id"] == 1
    assert second["display_id"] == 1


def test_display_id_not_reused_after_delete(client) -> None:
    _register(client)
    first = _create_problem(client, title="First")
    second = _create_problem(client, title="Second")

    deleted = client.delete(f"/api/problems/{second['id']}")
    third = _create_problem(client, title="Third")

    assert deleted.status_code == 200
    assert first["display_id"] == 1
    assert second["display_id"] == 2
    assert third["display_id"] == 3


def test_create_problem_without_login_returns_auth_required(client, monkeypatch) -> None:
    client.cookies.clear()
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.post("/api/problems", json=_problem_payload())

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_explicit_duplicate_slug_conflicts_for_same_user(client) -> None:
    _register(client)
    _create_problem(client, slug="two-sum")

    response = client.post("/api/problems", json=_problem_payload(title="Another", slug="two-sum"))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PROBLEM_SLUG_ALREADY_EXISTS"


def test_same_slug_allowed_for_different_users(client) -> None:
    _register(client, _user_payload("owner-a"))
    first = _create_problem(client, slug="shared-slug")
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))

    second = _create_problem(client, slug="shared-slug")

    assert second["slug"] == first["slug"]
    assert second["created_by_user_id"] != first["created_by_user_id"]


def test_generated_slug_adds_suffix_on_conflict(client) -> None:
    _register(client)
    first = _create_problem(client, title="Same Title")
    second = _create_problem(client, title="Same Title")

    assert first["slug"] == "same-title"
    assert second["slug"] == "same-title-2"


def test_invalid_problem_fields_return_validation_error(client) -> None:
    _register(client)

    difficulty = client.post("/api/problems", json=_problem_payload(difficulty="expert"))
    minutes = client.post("/api/problems", json=_problem_payload(estimated_minutes=0))

    assert difficulty.status_code == 422
    assert difficulty.json()["error"]["code"] == "VALIDATION_ERROR"
    assert minutes.status_code == 422
    assert minutes.json()["error"]["code"] == "VALIDATION_ERROR"


def test_topic_ids_associate_published_topics(client, published_topic) -> None:
    _register(client)

    problem = _create_problem(client, topic_ids=[str(published_topic.id), str(published_topic.id)])

    assert len(problem["topic_tags"]) == 1
    assert problem["topic_tags"][0]["id"] == str(published_topic.id)


def test_topic_ids_reject_missing_or_unpublished_topics(client, db_session) -> None:
    _register(client)
    unpublished = Topic(
        title="Draft topic",
        slug=f"draft-{uuid4().hex}",
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

    missing = client.post("/api/problems", json=_problem_payload(topic_ids=[str(uuid4())]))
    draft = client.post("/api/problems", json=_problem_payload(topic_ids=[str(unpublished.id)]))

    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "TOPIC_NOT_FOUND"
    assert draft.status_code == 404
    assert draft.json()["error"]["code"] == "TOPIC_NOT_FOUND"


def test_list_only_returns_current_user_problems(client) -> None:
    _register(client, _user_payload("owner-a"))
    first = _create_problem(client, title="Owner A Problem")
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))
    _create_problem(client, title="Owner B Problem")

    response = client.get("/api/problems")

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["total"] == 1
    assert body["data"][0]["created_by_user_id"] != first["created_by_user_id"]


def test_list_problem_order_is_newest_first(client, db_session) -> None:
    user = _register(client)
    old = Problem(
        id=uuid4(),
        display_id=1,
        title="Old",
        slug="old",
        difficulty="beginner",
        description_markdown="Old",
        created_by_user_id=UUID(user["id"]),
        created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    new = Problem(
        id=uuid4(),
        display_id=2,
        title="New",
        slug="new",
        difficulty="beginner",
        description_markdown="New",
        created_by_user_id=UUID(user["id"]),
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )
    db_session.add_all([old, new])
    db_session.commit()

    response = client.get("/api/problems")

    assert response.status_code == 200
    assert [item["title"] for item in response.json()["data"][:2]] == ["New", "Old"]


def test_get_update_delete_are_owner_scoped(client) -> None:
    _register(client, _user_payload("owner-a"))
    problem = _create_problem(client)
    client.cookies.clear()
    _register(client, _user_payload("owner-b"))

    get_response = client.get(f"/api/problems/{problem['id']}")
    update_response = client.put(f"/api/problems/{problem['id']}", json={"title": "Nope"})
    delete_response = client.delete(f"/api/problems/{problem['id']}")

    assert get_response.status_code == 404
    assert get_response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"
    assert update_response.status_code == 404
    assert update_response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"
    assert delete_response.status_code == 404
    assert delete_response.json()["error"]["code"] == "PROBLEM_NOT_FOUND"


def test_update_problem_fields_slug_and_topics(client, published_topic) -> None:
    _register(client)
    problem = _create_problem(client, slug="original-slug")

    update = client.put(
        f"/api/problems/{problem['id']}",
        json={
            "title": "Updated title",
            "slug": " Original Slug ",
            "difficulty": "advanced",
            "topic_ids": [str(published_topic.id)],
        },
    )

    assert update.status_code == 200
    body = update.json()["data"]
    assert body["title"] == "Updated title"
    assert body["slug"] == "original-slug"
    assert body["difficulty"] == "advanced"
    assert body["topic_tags"][0]["id"] == str(published_topic.id)


def test_update_without_slug_keeps_existing_slug(client) -> None:
    _register(client)
    problem = _create_problem(client, title="Original Title")

    update = client.put(f"/api/problems/{problem['id']}", json={"title": "Changed Title"})

    assert update.status_code == 200
    assert update.json()["data"]["slug"] == problem["slug"]


def test_update_empty_or_conflicting_slug_returns_error(client) -> None:
    _register(client)
    first = _create_problem(client, slug="first")
    second = _create_problem(client, slug="second")

    empty = client.put(f"/api/problems/{first['id']}", json={"slug": "   "})
    conflict = client.put(f"/api/problems/{second['id']}", json={"slug": "first"})

    assert empty.status_code == 422
    assert empty.json()["error"]["code"] == "VALIDATION_ERROR"
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "PROBLEM_SLUG_ALREADY_EXISTS"


def test_delete_problem_hard_deletes(client) -> None:
    _register(client)
    problem = _create_problem(client)

    deleted = client.delete(f"/api/problems/{problem['id']}")
    fetched = client.get(f"/api/problems/{problem['id']}")

    assert deleted.status_code == 200
    assert deleted.json() == {"data": {"success": True}}
    assert fetched.status_code == 404
    assert fetched.json()["error"]["code"] == "PROBLEM_NOT_FOUND"


def test_display_id_unique_constraint_exists(db_session) -> None:
    rows = db_session.execute(
        text(
            """
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'problems'
              AND constraint_type = 'UNIQUE'
              AND constraint_name = 'uq_problems_user_display_id'
            """
        )
    ).all()

    assert rows


def test_problem_counter_initializes_next_display_id(client, db_session) -> None:
    user = _register(client)
    first = _create_problem(client)

    counter = db_session.get(UserProblemCounter, UUID(user["id"]))

    assert first["display_id"] == 1
    assert counter is not None
    assert counter.next_display_id == 2


def test_dev_user_fallback_owns_problem(client, dev_user, db_session) -> None:
    client.cookies.clear()

    problem = _create_problem(client)

    assert problem["created_by_user_id"] == str(dev_user.id)
    db_session.execute(delete(Problem).where(Problem.id == problem["id"]))
    db_session.commit()
