from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select

from app.models.learning_record import LearningRecord
from app.models.topic import Topic
from app.models.user import User


def create_topic(
    db_session,
    *,
    title: str,
    category: str = "Dashboard Test",
    order_index: int = 1,
    difficulty_score: int = 3,
    estimated_minutes: int = 20,
) -> Topic:
    topic = Topic(
        title=title,
        slug=f"{title.lower().replace(' ', '-')}-{uuid4().hex}",
        category=category,
        level="beginner",
        difficulty_score=difficulty_score,
        summary=f"{title} summary",
        content_markdown=f"{title} content",
        estimated_minutes=estimated_minutes,
        status="published",
        published_at=datetime.now(timezone.utc),
        order_index=order_index,
    )
    db_session.add(topic)
    db_session.commit()
    return topic


def create_record(
    db_session,
    *,
    user: User,
    topic: Topic,
    status: str,
    progress_percent: int,
    mastery_level: int,
    last_studied_at: datetime,
    review_count: int = 0,
) -> LearningRecord:
    record = LearningRecord(
        user_id=user.id,
        topic_id=topic.id,
        status=status,
        progress_percent=progress_percent,
        mastery_level=mastery_level,
        review_count=review_count,
        last_studied_at=last_studied_at,
    )
    db_session.add(record)
    db_session.commit()
    return record


def ensure_record(
    db_session,
    *,
    user: User,
    topic: Topic,
    status: str,
    progress_percent: int,
    mastery_level: int,
    last_studied_at: datetime,
) -> LearningRecord:
    record = db_session.scalar(
        select(LearningRecord).where(
            LearningRecord.user_id == user.id,
            LearningRecord.topic_id == topic.id,
        )
    )
    if record is None:
        return create_record(
            db_session,
            user=user,
            topic=topic,
            status=status,
            progress_percent=progress_percent,
            mastery_level=mastery_level,
            last_studied_at=last_studied_at,
        )

    record.status = status
    record.progress_percent = progress_percent
    record.mastery_level = mastery_level
    record.last_studied_at = last_studied_at
    db_session.commit()
    return record


def test_dashboard_summary_empty_learning_records_recommends_unstarted_topics(
    client,
    db_session,
    dev_user,
) -> None:
    topic = create_topic(db_session, title="Dashboard Empty Topic", order_index=-100)

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total_topics"] >= 1
    assert body["not_started_topics"] >= 1
    assert body["recent_activity"] == []
    assert body["review_queue"] == []
    assert body["next_steps"][0]["topic_id"] == str(topic.id)
    assert body["next_steps"][0]["rank"] == 1
    assert body["next_steps"][0]["reason"] == "Next published topic with no learning record"


def test_dashboard_summary_returns_mixed_progress_and_category_progress(
    client,
    db_session,
    dev_user,
) -> None:
    now = datetime.now(timezone.utc)
    learning_topic = create_topic(
        db_session,
        title="Dashboard Learning Topic",
        category="Dashboard Arrays",
        estimated_minutes=30,
    )
    mastered_topic = create_topic(
        db_session,
        title="Dashboard Mastered Topic",
        category="Dashboard Arrays",
        estimated_minutes=40,
    )
    create_topic(
        db_session,
        title="Dashboard Unstarted Topic",
        category="Dashboard Strings",
        estimated_minutes=50,
    )
    create_record(
        db_session,
        user=dev_user,
        topic=learning_topic,
        status="learning",
        progress_percent=50,
        mastery_level=2,
        last_studied_at=now - timedelta(hours=2),
    )
    create_record(
        db_session,
        user=dev_user,
        topic=mastered_topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now - timedelta(hours=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["learning_topics"] >= 1
    assert body["mastered_topics"] >= 1
    assert body["started_topics"] >= 2
    assert body["total_estimated_minutes"] >= 120
    assert body["completed_estimated_minutes"] >= 40

    arrays = next(item for item in body["category_progress"] if item["category"] == "Dashboard Arrays")
    assert arrays["total_topics"] == 2
    assert arrays["started_topics"] == 2
    assert arrays["mastered_topics"] == 1
    assert arrays["progress_percent"] == 50
    assert arrays["estimated_minutes"] == 70
    assert arrays["completed_estimated_minutes"] == 40

    statuses = {item["status"]: item for item in body["status_counts"]}
    assert set(statuses) == {"not_started", "learning", "mastered"}
    assert statuses["learning"]["count"] >= 1
    assert statuses["mastered"]["count"] >= 1


def test_dashboard_recent_activity_is_sorted_and_limited(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topics = [
        create_topic(db_session, title=f"Dashboard Recent {index}", category="Dashboard Recent", order_index=index)
        for index in range(6)
    ]
    for index, topic in enumerate(topics):
        create_record(
            db_session,
            user=dev_user,
            topic=topic,
            status="learning",
            progress_percent=50,
            mastery_level=2,
            last_studied_at=now + timedelta(minutes=index),
        )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    recent = response.json()["data"]["recent_activity"]
    assert len(recent) == 5
    recent_titles = [item["title"] for item in recent]
    assert recent_titles[:5] == [
        "Dashboard Recent 5",
        "Dashboard Recent 4",
        "Dashboard Recent 3",
        "Dashboard Recent 2",
        "Dashboard Recent 1",
    ]


def test_dashboard_review_queue_rules(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    learning_topic = create_topic(db_session, title="Dashboard Review Learning")
    not_started_topic = create_topic(db_session, title="Dashboard Review Not Started")
    mastered_topic = create_topic(db_session, title="Dashboard Review Mastered")
    create_record(
        db_session,
        user=dev_user,
        topic=learning_topic,
        status="learning",
        progress_percent=50,
        mastery_level=2,
        last_studied_at=now - timedelta(days=2),
    )
    create_record(
        db_session,
        user=dev_user,
        topic=not_started_topic,
        status="not_started",
        progress_percent=0,
        mastery_level=0,
        last_studied_at=now - timedelta(days=3),
    )
    create_record(
        db_session,
        user=dev_user,
        topic=mastered_topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now - timedelta(days=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    review_queue = response.json()["data"]["review_queue"]
    review_ids = {item["topic_id"] for item in review_queue}
    assert str(learning_topic.id) in review_ids
    assert str(not_started_topic.id) not in review_ids
    assert str(mastered_topic.id) not in review_ids
    assert next(item for item in review_queue if item["topic_id"] == str(learning_topic.id))["reason"] == (
        "Learning topic needs another review"
    )


def test_dashboard_next_steps_fallbacks_to_non_mastered_when_all_topics_started(
    client,
    db_session,
    dev_user,
) -> None:
    now = datetime.now(timezone.utc)
    low_mastery_topic = create_topic(db_session, title="Dashboard Low Mastery", category="Dashboard Fallback")
    high_mastery_topic = create_topic(db_session, title="Dashboard High Mastery", category="Dashboard Fallback")
    for topic in db_session.scalars(select(Topic).where(Topic.status == "published")).all():
        ensure_record(
            db_session,
            user=dev_user,
            topic=topic,
            status="mastered",
            progress_percent=100,
            mastery_level=5,
            last_studied_at=now - timedelta(days=5),
        )
    ensure_record(
        db_session,
        user=dev_user,
        topic=low_mastery_topic,
        status="learning",
        progress_percent=40,
        mastery_level=1,
        last_studied_at=now,
    )
    ensure_record(
        db_session,
        user=dev_user,
        topic=high_mastery_topic,
        status="learning",
        progress_percent=80,
        mastery_level=4,
        last_studied_at=now - timedelta(hours=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    category_steps = [
        item for item in response.json()["data"]["next_steps"] if item["category"] == "Dashboard Fallback"
    ]
    assert category_steps[0]["topic_id"] == str(low_mastery_topic.id)
    assert category_steps[0]["rank"] == 1
    assert category_steps[0]["reason"] == "Continue a topic that is not mastered yet"


def test_dashboard_next_steps_empty_when_all_topics_mastered(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topic = create_topic(db_session, title="Dashboard All Mastered", category="Dashboard Complete")
    for published_topic in db_session.scalars(select(Topic).where(Topic.status == "published")).all():
        ensure_record(
            db_session,
            user=dev_user,
            topic=published_topic,
            status="mastered",
            progress_percent=100,
            mastery_level=5,
            last_studied_at=now,
        )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    category_steps = [
        item for item in response.json()["data"]["next_steps"] if item["category"] == "Dashboard Complete"
    ]
    assert category_steps == []


def test_dashboard_ignores_other_users_records(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topic = create_topic(db_session, title="Dashboard Isolation", category="Dashboard Isolation", order_index=-50)
    other_user = User(
        id=uuid4(),
        email=f"other-{uuid4()}@algomentor.local",
        username=f"other_{uuid4().hex[:8]}",
        learning_stage="beginner",
        target_track="algorithm_basics",
    )
    db_session.add(other_user)
    db_session.commit()
    create_record(
        db_session,
        user=other_user,
        topic=topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert str(topic.id) not in {item["topic_id"] for item in body["recent_activity"]}
    assert body["next_steps"][0]["topic_id"] == str(topic.id)
