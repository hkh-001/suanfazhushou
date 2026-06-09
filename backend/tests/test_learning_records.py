from sqlalchemy import select

from app.models.learning_record import LearningRecord


def test_upsert_learning_record_creates_record(client, db_session, dev_user, published_topic) -> None:
    response = client.post(
        "/api/learning/records",
        json={
            "topic_id": str(published_topic.id),
            "status": "learning",
            "progress_percent": 40,
            "mastery_level": 2,
            "note": "正在学习",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["topic_id"] == str(published_topic.id)
    assert body["status"] == "learning"
    assert body["progress_percent"] == 40

    records = db_session.scalars(select(LearningRecord)).all()
    assert len(records) == 1


def test_upsert_learning_record_updates_existing_record(client, db_session, dev_user, published_topic) -> None:
    payload = {
        "topic_id": str(published_topic.id),
        "status": "learning",
        "progress_percent": 30,
        "mastery_level": 1,
        "note": "第一次提交",
    }
    first = client.post("/api/learning/records", json=payload)
    assert first.status_code == 200

    payload.update(
        {
            "status": "mastered",
            "progress_percent": 100,
            "mastery_level": 5,
            "note": "已经掌握",
        }
    )
    second = client.post("/api/learning/records", json=payload)

    assert second.status_code == 200
    body = second.json()["data"]
    assert body["status"] == "mastered"
    assert body["progress_percent"] == 100

    records = db_session.scalars(select(LearningRecord)).all()
    assert len(records) == 1
    assert records[0].status == "mastered"
