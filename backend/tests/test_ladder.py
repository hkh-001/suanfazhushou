from datetime import datetime, timezone
from uuid import UUID
from uuid import uuid4

from sqlalchemy import delete, select

from app.models.ladder import LadderTemplate, LearningPath, LearningPathNode, NodeUserProgress
from app.models.topic import Topic
from scripts.seed_ladder_templates import seed_ladder_templates


def _register(client, *, student_id: str | None = None, goal_track: str = "self_study", current_level: str = "beginner"):
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/auth/register",
        json={
            "student_id": student_id or f"ladder_{suffix}",
            "password": "password123",
            "name": "Ladder Student",
            "current_level": current_level,
            "goal_track": goal_track,
            "goal_description": "Build a steady learning path.",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]


def _template_data(*, first_slug: str | None = None, second_slug: str | None = None) -> dict:
    first = {
        "algorithm_key": "complexity",
        "title": "Complexity",
        "summary": "Learn growth rates.",
        "material_markdown": "# Complexity\n\nRead the material.",
        "resource_links": [{"title": "Reference", "url": "https://example.com", "source": "external"}],
    }
    second = {
        "algorithm_key": "sorting",
        "title": "Sorting",
        "summary": "Use ordering.",
        "material_markdown": "# Sorting\n\nRead the material.",
        "resource_links": [],
    }
    if first_slug:
        first["topic_slug"] = first_slug
    if second_slug:
        second["topic_slug"] = second_slug
    return {
        "phases": [
            {"title": "Foundation", "description": "Start here.", "nodes": [first]},
            {"title": "Patterns", "description": "Then practice patterns.", "nodes": [second]},
        ]
    }


def _add_template(
    db_session,
    *,
    goal_track: str = "self_study",
    current_level: str = "beginner",
    version: int = 1,
    is_default: bool = True,
    template_data: dict | None = None,
) -> LadderTemplate:
    template = LadderTemplate(
        goal_track=goal_track,
        current_level=current_level,
        name=f"{goal_track}-{current_level}",
        description="Test ladder template",
        template_data=template_data or _template_data(),
        version=version,
        is_default=is_default,
    )
    db_session.add(template)
    db_session.commit()
    return template


def _add_topic(db_session, *, slug: str, status: str = "published") -> Topic:
    topic = Topic(
        title=f"Topic {slug}",
        slug=slug,
        category="Basics",
        level="beginner",
        difficulty_score=3,
        summary="Topic summary",
        content_markdown="Topic content",
        estimated_minutes=20,
        status=status,
        published_at=datetime.now(timezone.utc) if status == "published" else None,
        order_index=1,
    )
    db_session.add(topic)
    db_session.commit()
    return topic


def _nodes(body: dict) -> list[dict]:
    return [node for phase in body["data"]["phases"] for node in phase["nodes"]]


def test_get_ladder_creates_active_path_and_progress(client, db_session) -> None:
    _add_template(db_session)
    user = _register(client)

    response = client.get("/api/ladder")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["path"]["status"] == "active"
    assert body["path"]["goal_track"] == "self_study"
    assert body["current_node_id"] == _nodes(response.json())[0]["id"]
    assert _nodes(response.json())[0]["status"] == "unlocked"
    assert _nodes(response.json())[1]["status"] == "locked"

    user_id = UUID(user["id"])
    paths = db_session.scalars(select(LearningPath).where(LearningPath.user_id == user_id)).all()
    progress = db_session.scalars(select(NodeUserProgress).where(NodeUserProgress.user_id == user_id)).all()
    assert len(paths) == 1
    assert len(progress) == 2


def test_repeated_get_does_not_create_duplicate_path(client, db_session) -> None:
    _add_template(db_session)
    user = _register(client)

    first = client.get("/api/ladder")
    second = client.get("/api/ladder")

    assert first.status_code == 200
    assert second.status_code == 200
    paths = db_session.scalars(select(LearningPath).where(LearningPath.user_id == user["id"])).all()
    assert len(paths) == 1


def test_different_users_have_isolated_paths(client, db_session) -> None:
    _add_template(db_session)
    first_user = _register(client, student_id="ladder_user_a")
    first = client.get("/api/ladder")
    client.cookies.clear()
    second_user = _register(client, student_id="ladder_user_b")
    second = client.get("/api/ladder")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"]["path"]["id"] != second.json()["data"]["path"]["id"]
    assert len(db_session.scalars(select(LearningPath).where(LearningPath.user_id == UUID(first_user["id"]))).all()) == 1
    assert len(db_session.scalars(select(LearningPath).where(LearningPath.user_id == UUID(second_user["id"]))).all()) == 1


def test_template_selection_exact_and_fallbacks(client, db_session) -> None:
    exact = _add_template(db_session, goal_track="lanqiao", current_level="elementary")
    _add_template(db_session, goal_track="icpc", current_level="beginner")
    _add_template(db_session, goal_track="self_study", current_level="beginner")

    _register(client, student_id="exact_ladder", goal_track="lanqiao", current_level="elementary")
    exact_response = client.get("/api/ladder")
    assert exact_response.status_code == 200
    assert exact_response.json()["data"]["path"]["template_name"] == exact.name

    client.cookies.clear()
    _register(client, student_id="closest_ladder", goal_track="icpc", current_level="improvement")
    closest_response = client.get("/api/ladder")
    assert closest_response.status_code == 200
    assert closest_response.json()["data"]["path"]["goal_track"] == "icpc"
    assert closest_response.json()["data"]["path"]["current_level"] == "beginner"

    client.cookies.clear()
    _register(client, student_id="self_study_ladder", goal_track="course", current_level="improvement")
    fallback_response = client.get("/api/ladder")
    assert fallback_response.status_code == 200
    assert fallback_response.json()["data"]["path"]["goal_track"] == "self_study"


def test_missing_template_returns_error(client, dev_user) -> None:
    response = client.get("/api/ladder")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LADDER_TEMPLATE_NOT_FOUND"


def test_material_complete_unlocks_next_node_and_is_idempotent(client, db_session) -> None:
    _add_template(db_session)
    _register(client)
    first = client.get("/api/ladder")
    node_ids = [node["id"] for node in _nodes(first.json())]

    locked = client.post(f"/api/ladder/nodes/{node_ids[1]}/material-complete")
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "NODE_LOCKED"

    complete = client.post(f"/api/ladder/nodes/{node_ids[0]}/material-complete")
    assert complete.status_code == 200
    nodes = _nodes(complete.json())
    assert nodes[0]["status"] == "material_done"
    assert nodes[1]["status"] == "unlocked"
    assert complete.json()["data"]["current_node_id"] == nodes[1]["id"]

    repeat = client.post(f"/api/ladder/nodes/{node_ids[0]}/material-complete")
    assert repeat.status_code == 200
    assert _nodes(repeat.json())[0]["status"] == "material_done"


def test_user_cannot_access_or_update_other_user_node(client, db_session) -> None:
    _add_template(db_session)
    _register(client, student_id="owner_ladder")
    owner_summary = client.get("/api/ladder")
    owner_node_id = _nodes(owner_summary.json())[0]["id"]
    client.cookies.clear()
    _register(client, student_id="other_ladder")
    client.get("/api/ladder")

    detail = client.get(f"/api/ladder/nodes/{owner_node_id}")
    complete = client.post(f"/api/ladder/nodes/{owner_node_id}/material-complete")

    assert detail.status_code == 404
    assert detail.json()["error"]["code"] == "LADDER_NODE_NOT_FOUND"
    assert complete.status_code == 404
    assert complete.json()["error"]["code"] == "LADDER_NODE_NOT_FOUND"


def test_node_detail_and_current_node_rules(client, db_session) -> None:
    _add_template(db_session)
    _register(client)
    summary = client.get("/api/ladder")
    first_node = _nodes(summary.json())[0]

    detail = client.get(f"/api/ladder/nodes/{first_node['id']}")

    assert detail.status_code == 200
    body = detail.json()["data"]
    assert body["id"] == first_node["id"]
    assert body["status"] == "unlocked"
    assert body["material_markdown"].startswith("# Complexity")
    assert body["resource_links"][0]["url"] == "https://example.com"


def test_topic_slug_binds_only_published_topics(client, db_session) -> None:
    published = _add_topic(db_session, slug=f"published-{uuid4().hex}", status="published")
    draft = _add_topic(db_session, slug=f"draft-{uuid4().hex}", status="draft")
    _add_template(db_session, template_data=_template_data(first_slug=published.slug, second_slug=draft.slug))
    _register(client)

    response = client.get("/api/ladder")
    nodes = _nodes(response.json())

    assert response.status_code == 200
    assert nodes[0]["topic_id"] == str(published.id)
    assert nodes[1]["topic_id"] is None


def test_seed_ladder_templates_is_idempotent(db_session, monkeypatch) -> None:
    class SessionContext:
        def __enter__(self):
            return db_session

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr("scripts.seed_ladder_templates.SessionLocal", lambda: SessionContext())

    seed_ladder_templates()
    seed_ladder_templates()

    templates = db_session.scalars(select(LadderTemplate)).all()
    keys = {(template.goal_track, template.current_level, template.version) for template in templates}
    assert len(templates) == 4
    assert len(keys) == 4


def test_no_algorithm_key_uniqueness_within_path(client, db_session) -> None:
    data = _template_data()
    data["phases"][1]["nodes"][0]["algorithm_key"] = "complexity"
    _add_template(db_session, template_data=data)
    _register(client)

    response = client.get("/api/ladder")

    assert response.status_code == 200
    assert [node["algorithm_key"] for node in _nodes(response.json())] == ["complexity", "complexity"]
