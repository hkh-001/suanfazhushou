from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, create_access_token
from app.models.ai_call_log import AICallLog
from app.models.interactive_lesson import InteractiveLesson
from app.models.learning_record import LearningRecord
from app.models.topic import Topic
from app.models.user import User
from app.schemas.openmaic import OpenMAICJobStatus
from app.services import interactive_lessons as lesson_service
from app.services.openmaic import OpenMAICClientError


class FakeOpenMAICClient:
    generated_payloads = []
    requested_jobs = []
    generate_result = OpenMAICJobStatus(status="submitted", job_id="job-123", poll_url="/jobs/job-123")
    refresh_result = OpenMAICJobStatus(
        status="completed",
        job_id="job-123",
        classroom_url="http://openmaic.local/classroom/job-123",
    )
    generate_error = None
    refresh_error = None

    async def generate_classroom(self, payload):
        FakeOpenMAICClient.generated_payloads.append(payload)
        if FakeOpenMAICClient.generate_error is not None:
            raise FakeOpenMAICClient.generate_error
        return FakeOpenMAICClient.generate_result

    async def get_job(self, job_id: str):
        FakeOpenMAICClient.requested_jobs.append(job_id)
        if FakeOpenMAICClient.refresh_error is not None:
            raise FakeOpenMAICClient.refresh_error
        return FakeOpenMAICClient.refresh_result


def _login_as(client, user: User) -> None:
    client.cookies.set(SESSION_COOKIE_NAME, create_access_token(user.id))


def _enable_openmaic(monkeypatch) -> None:
    monkeypatch.setattr(settings, "enable_openmaic_integration", True)
    monkeypatch.setattr(settings, "openmaic_base_url", "http://openmaic.local")
    FakeOpenMAICClient.generated_payloads = []
    FakeOpenMAICClient.requested_jobs = []
    FakeOpenMAICClient.generate_result = OpenMAICJobStatus(
        status="submitted",
        job_id="job-123",
        poll_url="/jobs/job-123",
    )
    FakeOpenMAICClient.refresh_result = OpenMAICJobStatus(
        status="completed",
        job_id="job-123",
        classroom_url="http://openmaic.local/classroom/job-123",
    )
    FakeOpenMAICClient.generate_error = None
    FakeOpenMAICClient.refresh_error = None
    monkeypatch.setattr(lesson_service, "get_openmaic_client", lambda: FakeOpenMAICClient())


def _create_other_user(db_session) -> User:
    user = User(
        email=f"user-{uuid4()}@algomentor.local",
        username=f"user_{uuid4().hex[:8]}",
        student_id=f"user_{uuid4().hex[:8]}",
        name="普通用户",
        current_level="beginner",
        goal_track="self_study",
        role="user",
        learning_stage="beginner",
        target_track="self_study",
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_interactive_lesson_requires_auth(client, monkeypatch, published_topic) -> None:
    monkeypatch.setattr(settings, "enable_dev_user", False)

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_REQUIRED"


def test_interactive_lesson_feature_disabled(client, dev_user, monkeypatch, published_topic) -> None:
    monkeypatch.setattr(settings, "enable_openmaic_integration", False)

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FEATURE_DISABLED"


def test_interactive_lesson_requires_published_topic(client, dev_user, db_session, monkeypatch) -> None:
    _enable_openmaic(monkeypatch)
    draft = Topic(
        title="未发布主题",
        slug=f"draft-{uuid4().hex}",
        category="基础",
        level="beginner",
        difficulty_score=2,
        summary="未发布",
        content_markdown="内容",
        estimated_minutes=10,
        status="draft",
        order_index=1,
    )
    db_session.add(draft)
    db_session.commit()

    response = client.post(f"/api/topics/{draft.id}/interactive-lessons")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "TOPIC_NOT_FOUND"


def test_create_interactive_lesson_saves_submitted_status(client, dev_user, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["topic_id"] == str(published_topic.id)
    assert data["status"] == "submitted"
    assert data["classroom_url"] is None
    assert data["error_code"] is None


def test_create_interactive_lesson_uses_safe_topic_requirement(client, dev_user, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    requirement = FakeOpenMAICClient.generated_payloads[0].requirement
    assert published_topic.title in requirement
    assert published_topic.summary in requirement
    assert dev_user.current_level in requirement
    assert dev_user.goal_track in requirement
    assert dev_user.student_id not in requirement
    assert "学号" in requirement
    assert "完整学习历史" in requirement
    assert "提交代码" in requirement
    assert "隐藏测试" in requirement
    assert "correct_option_id" not in requirement
    assert "exam_payload" not in requirement


def test_openmaic_unknown_status_is_stored_as_processing(client, dev_user, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    FakeOpenMAICClient.generate_result = OpenMAICJobStatus(status="unknown", job_id="job-unknown")

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "processing"


def test_completed_without_classroom_url_remains_processing(client, dev_user, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    FakeOpenMAICClient.generate_result = OpenMAICJobStatus(status="completed", job_id="job-no-url")

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "processing"
    assert response.json()["data"]["classroom_url"] is None


def test_generate_failure_keeps_failed_lesson_with_safe_message(
    client,
    dev_user,
    db_session,
    monkeypatch,
    published_topic,
) -> None:
    _enable_openmaic(monkeypatch)
    FakeOpenMAICClient.generate_error = OpenMAICClientError(
        "OPENMAIC_TIMEOUT",
        "raw upstream timeout with secret",
        status_code=504,
    )

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 504
    assert response.json()["error"]["code"] == "OPENMAIC_TIMEOUT"
    lesson = db_session.query(InteractiveLesson).filter_by(user_id=dev_user.id, topic_id=published_topic.id).one()
    assert lesson.status == "failed"
    assert lesson.error_code == "OPENMAIC_TIMEOUT"
    assert lesson.error_message == "互动课堂服务请求超时，请稍后重试。"
    assert "secret" not in lesson.error_message


def test_reuses_recent_active_lesson(client, dev_user, db_session, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    existing = InteractiveLesson(
        user_id=dev_user.id,
        topic_id=published_topic.id,
        title="已有课堂",
        status="processing",
        openmaic_job_id="job-existing",
    )
    db_session.add(existing)
    db_session.commit()

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(existing.id)
    assert FakeOpenMAICClient.generated_payloads == []


def test_failed_lesson_does_not_block_regeneration(client, dev_user, db_session, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    failed = InteractiveLesson(
        user_id=dev_user.id,
        topic_id=published_topic.id,
        title="失败课堂",
        status="failed",
        error_code="OPENMAIC_TIMEOUT",
        error_message="互动课堂服务请求超时，请稍后重试。",
    )
    db_session.add(failed)
    db_session.commit()

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    assert response.json()["data"]["id"] != str(failed.id)
    assert len(FakeOpenMAICClient.generated_payloads) == 1


def test_other_user_cannot_read_or_refresh_lesson(client, dev_user, db_session, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    lesson = InteractiveLesson(
        user_id=dev_user.id,
        topic_id=published_topic.id,
        title="私有课堂",
        status="processing",
        openmaic_job_id="job-private",
    )
    db_session.add(lesson)
    db_session.commit()
    other = _create_other_user(db_session)
    _login_as(client, other)

    read_response = client.get(f"/api/interactive-lessons/{lesson.id}")
    refresh_response = client.post(f"/api/interactive-lessons/{lesson.id}/refresh")

    assert read_response.status_code == 404
    assert read_response.json()["error"]["code"] == "INTERACTIVE_LESSON_NOT_FOUND"
    assert refresh_response.status_code == 404
    assert refresh_response.json()["error"]["code"] == "INTERACTIVE_LESSON_NOT_FOUND"


def test_refresh_updates_completed_lesson(client, dev_user, db_session, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    lesson = InteractiveLesson(
        user_id=dev_user.id,
        topic_id=published_topic.id,
        title="生成中课堂",
        status="processing",
        openmaic_job_id="job-123",
    )
    db_session.add(lesson)
    db_session.commit()

    response = client.post(f"/api/interactive-lessons/{lesson.id}/refresh")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["classroom_url"] == "http://openmaic.local/classroom/job-123"
    assert data["completed_at"] is not None
    assert FakeOpenMAICClient.requested_jobs == ["job-123"]


def test_refresh_job_not_found_marks_failed_safely(client, dev_user, db_session, monkeypatch, published_topic) -> None:
    _enable_openmaic(monkeypatch)
    lesson = InteractiveLesson(
        user_id=dev_user.id,
        topic_id=published_topic.id,
        title="生成中课堂",
        status="processing",
        openmaic_job_id="missing",
    )
    db_session.add(lesson)
    db_session.commit()
    FakeOpenMAICClient.refresh_error = OpenMAICClientError(
        "OPENMAIC_JOB_NOT_FOUND",
        "raw missing job",
        status_code=404,
    )

    response = client.post(f"/api/interactive-lessons/{lesson.id}/refresh")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "failed"
    assert data["error_code"] == "OPENMAIC_JOB_NOT_FOUND"
    assert data["error_message"] == "互动课堂任务不存在或已过期，请重新生成。"


def test_interactive_lesson_does_not_touch_ai_logs_or_learning_records(
    client,
    dev_user,
    db_session,
    monkeypatch,
    published_topic,
) -> None:
    _enable_openmaic(monkeypatch)
    db_session.add(
        LearningRecord(
            user_id=dev_user.id,
            topic_id=published_topic.id,
            status="learning",
            progress_percent=20,
            mastery_level=1,
        )
    )
    db_session.commit()

    response = client.post(f"/api/topics/{published_topic.id}/interactive-lessons")

    assert response.status_code == 200
    assert db_session.query(AICallLog).filter_by(user_id=dev_user.id).count() == 0
    record = db_session.query(LearningRecord).filter_by(user_id=dev_user.id, topic_id=published_topic.id).one()
    assert record.status == "learning"
    assert record.progress_percent == 20


def test_get_interactive_lesson_returns_current_user_lesson(client, dev_user, db_session, published_topic) -> None:
    lesson = InteractiveLesson(
        user_id=dev_user.id,
        topic_id=published_topic.id,
        title="已完成课堂",
        status="completed",
        openmaic_job_id="job-done",
        openmaic_classroom_url="http://openmaic.local/classroom/job-done",
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(lesson)
    db_session.commit()

    response = client.get(f"/api/interactive-lessons/{lesson.id}")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"
    assert response.json()["data"]["classroom_url"] == "http://openmaic.local/classroom/job-done"
