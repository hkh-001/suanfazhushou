from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.learning_records import upsert_learning_record
from app.repositories.topics import get_published_topic
from app.schemas.learning import LearningRecordRead, LearningRecordUpsert


def save_learning_record(db: Session, *, user: User, payload: LearningRecordUpsert) -> LearningRecordRead:
    topic = get_published_topic(db, payload.topic_id)
    if topic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TOPIC_NOT_FOUND", "message": "Topic not found"},
        )
    record = upsert_learning_record(db, user_id=user.id, payload=payload)
    return LearningRecordRead.model_validate(record, from_attributes=True)
