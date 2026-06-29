from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from tempfile import gettempdir
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.ai_call_log import AICallLog
from app.models.code_review import CodeReview
from app.models.interactive_lesson import InteractiveLesson
from app.models.ladder import LadderTemplate, LearningPath, LearningPathNode, NodeUserProgress
from app.models.learning_record import LearningRecord
from app.models.mistake_note import MistakeNote
from app.models.problem import Problem, UserProblemCounter
from app.models.submission import Submission
from app.models.topic import Topic
from app.models.user import User
from app.models.user_ai_setting import UserAISetting
from app.services.settings.ai_runtime_settings import clear_runtime_ai_settings


@pytest.fixture(autouse=True)
def reset_runtime_ai_settings(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    test_settings_path = Path(gettempdir()) / f"algomentor-runtime-ai-settings-{uuid4().hex}.json"
    monkeypatch.setattr(settings, "persistent_ai_settings_path", str(test_settings_path))
    needs_db_cleanup = {
        "client",
        "db_session",
        "dev_user",
        "published_topic",
    }.intersection(request.fixturenames) and request.module.__name__ != "tests.test_settings"
    if needs_db_cleanup:
        db_session = request.getfixturevalue("db_session")
        db_session.execute(delete(NodeUserProgress))
        db_session.execute(delete(LearningPathNode))
        db_session.execute(delete(LearningPath))
        db_session.execute(delete(LadderTemplate))
        db_session.execute(delete(InteractiveLesson))
        db_session.execute(delete(MistakeNote))
        db_session.execute(delete(CodeReview))
        db_session.execute(delete(AICallLog))
        db_session.execute(delete(UserAISetting))
        db_session.commit()
    clear_runtime_ai_settings()
    try:
        yield
    finally:
        clear_runtime_ai_settings()


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    transaction = connection.begin()
    TestingSessionLocal = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
def dev_user(db_session: Session) -> Generator[User, None, None]:
    previous_enable_dev_user = settings.enable_dev_user
    settings.enable_dev_user = True
    dev_user_id = UUID(settings.dev_user_id)
    db_session.execute(delete(AICallLog).where(AICallLog.user_id == dev_user_id))
    db_session.execute(delete(LearningRecord).where(LearningRecord.user_id == dev_user_id))
    db_session.execute(delete(Problem).where(Problem.created_by_user_id == dev_user_id))
    db_session.execute(delete(Submission).where(Submission.user_id == dev_user_id))
    db_session.execute(delete(InteractiveLesson).where(InteractiveLesson.user_id == dev_user_id))
    db_session.execute(delete(NodeUserProgress).where(NodeUserProgress.user_id == dev_user_id))
    db_session.execute(delete(LearningPath).where(LearningPath.user_id == dev_user_id))
    db_session.execute(delete(UserProblemCounter).where(UserProblemCounter.user_id == dev_user_id))
    db_session.execute(delete(UserAISetting).where(UserAISetting.user_id == dev_user_id))
    db_session.execute(delete(User).where(User.id == dev_user_id))
    db_session.flush()
    user = User(
        id=dev_user_id,
        email=f"dev-{uuid4()}@algomentor.local",
        username=f"dev_{uuid4().hex[:8]}",
        student_id=f"dev_{uuid4().hex[:8]}",
        name="开发用户",
        current_level="beginner",
        goal_track="self_study",
        role="user",
        learning_stage="beginner",
        target_track="algorithm_basics",
    )
    db_session.add(user)
    db_session.commit()
    try:
        yield user
    finally:
        settings.enable_dev_user = previous_enable_dev_user


@pytest.fixture()
def admin_user(db_session: Session) -> User:
    user = User(
        email=f"admin-{uuid4()}@algomentor.local",
        username=f"admin_{uuid4().hex[:8]}",
        student_id=f"admin_{uuid4().hex[:8]}",
        name="Admin",
        current_level="improvement",
        goal_track="self_study",
        role="admin",
        learning_stage="improvement",
        target_track="self_study",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def published_topic(db_session: Session) -> Topic:
    topic = Topic(
        title="测试知识点",
        slug=f"test-topic-{uuid4().hex}",
        category="测试分类",
        level="beginner",
        difficulty_score=3,
        summary="用于 API 测试的知识点。",
        content_markdown="这是一段测试内容。",
        estimated_minutes=20,
        status="published",
        published_at=datetime.now(timezone.utc),
        order_index=1,
    )
    db_session.add(topic)
    db_session.commit()
    return topic
