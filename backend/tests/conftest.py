from collections.abc import Generator
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.topic import Topic
from app.models.user import User


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
def dev_user(db_session: Session) -> User:
    user = User(
        id=UUID(settings.dev_user_id),
        email=f"dev-{uuid4()}@algomentor.local",
        username=f"dev_{uuid4().hex[:8]}",
        learning_stage="beginner",
        target_track="algorithm_basics",
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
