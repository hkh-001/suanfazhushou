from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.learning_record import LearningRecord
from app.models.topic import Topic


def count_published_topics(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(Topic).where(Topic.status == "published")) or 0


def list_published_topics_with_learning(
    db: Session,
    *,
    user_id: UUID,
    page: int,
    page_size: int,
) -> list[tuple[Topic, LearningRecord | None]]:
    offset = (page - 1) * page_size
    stmt = (
        select(Topic, LearningRecord)
        .outerjoin(
            LearningRecord,
            and_(LearningRecord.topic_id == Topic.id, LearningRecord.user_id == user_id),
        )
        .where(Topic.status == "published")
        .order_by(Topic.category, Topic.order_index, Topic.created_at)
        .offset(offset)
        .limit(page_size)
    )
    return list(db.execute(stmt).all())


def get_published_topic_with_learning(
    db: Session,
    *,
    topic_id: UUID,
    user_id: UUID,
) -> tuple[Topic, LearningRecord | None] | None:
    stmt = (
        select(Topic, LearningRecord)
        .outerjoin(
            LearningRecord,
            and_(LearningRecord.topic_id == Topic.id, LearningRecord.user_id == user_id),
        )
        .where(Topic.id == topic_id, Topic.status == "published")
    )
    return db.execute(stmt).first()


def get_published_topic(db: Session, topic_id: UUID) -> Topic | None:
    return db.scalar(select(Topic).where(Topic.id == topic_id, Topic.status == "published"))
