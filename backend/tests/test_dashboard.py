def test_dashboard_summary_returns_counts(client, dev_user, published_topic) -> None:
    client.post(
        "/api/learning/records",
        json={
            "topic_id": str(published_topic.id),
            "status": "mastered",
            "progress_percent": 100,
            "mastery_level": 5,
            "note": "完成",
        },
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total_topics"] >= 1
    assert body["started_topics"] >= 1
    assert body["mastered_topics"] >= 1
    assert body["progress_percent"] >= 0
