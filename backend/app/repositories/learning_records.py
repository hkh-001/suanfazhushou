from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.learning_record import LearningRecord
from app.schemas.learning import LearningRecordUpsert


def get_learning_record(db: Session, *, user_id: UUID, topic_id: UUID) -> LearningRecord | None:
    return db.scalar(
        select(LearningRecord).where(
            LearningRecord.user_id == user_id,
            LearningRecord.topic_id == topic_id,
        )
    )


def upsert_learning_record(
    db: Session,
    *,
    user_id: UUID,
    payload: LearningRecordUpsert,
) -> LearningRecord:
    record = get_learning_record(db, user_id=user_id, topic_id=payload.topic_id)
    now = datetime.now(timezone.utc)
    if record is None:
        record = LearningRecord(
            user_id=user_id,
            topic_id=payload.topic_id,
            status=payload.status,
            progress_percent=payload.progress_percent,
            mastery_level=payload.mastery_level,
            note=payload.note,
            review_count=0,
            last_studied_at=now,
        )
        db.add(record)
    else:
        record.status = payload.status
        record.progress_percent = payload.progress_percent
        record.mastery_level = payload.mastery_level
        record.note = payload.note
        record.review_count += 1
        record.last_studied_at = now

    db.commit()
    db.refresh(record)
    return record
