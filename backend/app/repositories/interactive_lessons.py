from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.interactive_lesson import InteractiveLesson


REUSABLE_LESSON_STATUSES = ("submitted", "processing", "completed")


def get_recent_reusable_lesson(db: Session, *, user_id: UUID, topic_id: UUID) -> InteractiveLesson | None:
    stmt = (
        select(InteractiveLesson)
        .where(
            InteractiveLesson.user_id == user_id,
            InteractiveLesson.topic_id == topic_id,
            InteractiveLesson.status.in_(REUSABLE_LESSON_STATUSES),
        )
        .order_by(InteractiveLesson.created_at.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def create_pending_lesson(db: Session, *, user_id: UUID, topic_id: UUID, title: str) -> InteractiveLesson:
    lesson = InteractiveLesson(user_id=user_id, topic_id=topic_id, title=title, status="pending")
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def get_lesson_for_user(db: Session, *, lesson_id: UUID, user_id: UUID) -> InteractiveLesson | None:
    stmt = select(InteractiveLesson).where(InteractiveLesson.id == lesson_id, InteractiveLesson.user_id == user_id)
    return db.scalar(stmt)


def update_lesson_status(
    db: Session,
    *,
    lesson: InteractiveLesson,
    status: str,
    job_id: str | None,
    poll_url: str | None,
    classroom_url: str | None,
    error_code: str | None = None,
    error_message: str | None = None,
) -> InteractiveLesson:
    lesson.status = status
    lesson.openmaic_job_id = job_id
    lesson.openmaic_poll_url = poll_url
    lesson.openmaic_classroom_url = classroom_url
    lesson.error_code = error_code
    lesson.error_message = error_message
    lesson.completed_at = datetime.now(timezone.utc) if status == "completed" else None
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


def mark_lesson_failed(
    db: Session,
    *,
    lesson: InteractiveLesson,
    error_code: str,
    error_message: str,
) -> InteractiveLesson:
    lesson.status = "failed"
    lesson.error_code = error_code
    lesson.error_message = error_message
    lesson.completed_at = None
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson
