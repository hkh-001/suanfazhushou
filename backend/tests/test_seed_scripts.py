from __future__ import annotations

from sqlalchemy import select

from app.models.ladder import LadderTemplate
from app.models.prompt_template import PromptTemplate
from app.models.topic import Topic, TopicDependency
from app.models.user import User
from scripts import init_dev, seed_admin, seed_ladder_templates, seed_prompt_templates, seed_topics


class SessionContext:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, traceback):
        return False


def _patch_session(monkeypatch, module, db_session) -> None:
    monkeypatch.setattr(module, "SessionLocal", lambda: SessionContext(db_session))


def test_seed_topics_is_idempotent_and_has_core_topics(db_session, monkeypatch) -> None:
    _patch_session(monkeypatch, seed_topics, db_session)

    seed_topics.main()
    seed_topics.main()

    expected_slugs = {item["slug"] for item in seed_topics.TOPICS}
    slugs = set(db_session.scalars(select(Topic.slug)))
    assert expected_slugs.issubset(slugs)
    assert len(expected_slugs) >= 20
    assert len(expected_slugs) == len(seed_topics.TOPICS)
    assert {
        "time-complexity",
        "binary-search",
        "dfs",
        "dynamic-programming-basics",
        "union-find",
    }.issubset(slugs)

    statuses = set(db_session.scalars(select(Topic.status).where(Topic.slug.in_(expected_slugs))))
    assert statuses == {"published"}

    topics_by_slug = {topic.slug: topic for topic in db_session.scalars(select(Topic).where(Topic.slug.in_(expected_slugs)))}
    dependency_pairs = {
        (dependency.topic_id, dependency.depends_on_topic_id)
        for dependency in db_session.scalars(select(TopicDependency))
    }
    for topic_slug, depends_on_slug in seed_topics.TOPIC_DEPENDENCIES:
        assert (topics_by_slug[topic_slug].id, topics_by_slug[depends_on_slug].id) in dependency_pairs


def test_seed_ladder_templates_is_idempotent(db_session, monkeypatch) -> None:
    _patch_session(monkeypatch, seed_ladder_templates, db_session)

    seed_ladder_templates.seed_ladder_templates()
    seed_ladder_templates.seed_ladder_templates()

    expected_keys = {
        (item["goal_track"], item["current_level"], 1)
        for item in seed_ladder_templates.DEFAULT_TEMPLATES
    }
    found_keys = {
        (template.goal_track, template.current_level, template.version)
        for template in db_session.scalars(select(LadderTemplate))
    }
    assert expected_keys.issubset(found_keys)


def test_seed_prompt_templates_is_idempotent(db_session, monkeypatch) -> None:
    _patch_session(monkeypatch, seed_prompt_templates, db_session)

    seed_prompt_templates.seed_prompt_templates()
    seed_prompt_templates.seed_prompt_templates()

    expected_keys = {item["template_key"] for item in seed_prompt_templates.TEMPLATES}
    found_keys = {
        (template.template_key, template.version)
        for template in db_session.scalars(select(PromptTemplate).where(PromptTemplate.template_key.in_(expected_keys)))
    }
    assert {(item["template_key"], item["version"]) for item in seed_prompt_templates.TEMPLATES}.issubset(found_keys)


def test_init_dev_skips_admin_when_password_missing(monkeypatch) -> None:
    calls: list[str] = []
    previous_password = init_dev.settings.dev_admin_password
    init_dev.settings.dev_admin_password = ""
    monkeypatch.setattr(init_dev, "run_migrations", lambda: calls.append("migrations"))
    monkeypatch.setattr(init_dev, "seed_base_data", lambda: calls.append("base"))
    monkeypatch.setattr(init_dev, "print_summary", lambda *, admin_seeded: calls.append(f"summary:{admin_seeded}"))
    try:
        init_dev.main()
    finally:
        init_dev.settings.dev_admin_password = previous_password

    assert calls == ["migrations", "base", "summary:False"]


def test_seed_admin_creates_admin_when_password_configured(db_session, monkeypatch) -> None:
    _patch_session(monkeypatch, seed_admin, db_session)
    previous_password = seed_admin.settings.dev_admin_password
    seed_admin.settings.dev_admin_password = "local-admin-password"
    try:
        seed_admin.main()
    finally:
        seed_admin.settings.dev_admin_password = previous_password

    admin = db_session.scalar(select(User).where(User.student_id == "admin"))
    assert admin is not None
    assert admin.role == "admin"
    assert admin.hashed_password is not None
    assert admin.hashed_password != "local-admin-password"
