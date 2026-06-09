from uuid import uuid4


def test_get_topics_returns_paginated_topics(client, dev_user, published_topic) -> None:
    response = client.get("/api/topics")

    assert response.status_code == 200
    body = response.json()
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["page_size"] == 20
    assert body["pagination"]["total"] >= 1
    assert body["data"][0]["learning_status"]["status"] == "not_started"


def test_get_topic_detail_returns_topic(client, dev_user, published_topic) -> None:
    response = client.get(f"/api/topics/{published_topic.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["id"] == str(published_topic.id)
    assert body["data"]["content_markdown"] == published_topic.content_markdown
    assert body["data"]["learning_status"]["status"] == "not_started"


def test_get_missing_topic_returns_404(client, dev_user) -> None:
    missing_topic_id = uuid4()

    response = client.get(f"/api/topics/{missing_topic_id}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "TOPIC_NOT_FOUND",
            "message": "Topic not found",
        }
    }
