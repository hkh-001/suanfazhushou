from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.learning_record import LearningRecord
from app.models.topic import Topic


def get_dashboard_counts(db: Session, *, user_id: UUID) -> dict[str, int]:
    total_topics = db.scalar(select(func.count()).select_from(Topic).where(Topic.status == "published")) or 0
    started_topics = (
        db.scalar(
            select(func.count())
            .select_from(LearningRecord)
            .join(Topic, Topic.id == LearningRecord.topic_id)
            .where(
                LearningRecord.user_id == user_id,
                Topic.status == "published",
                LearningRecord.status.in_(["learning", "mastered"]),
            )
        )
        or 0
    )
    learning_topics = (
        db.scalar(
            select(func.count())
            .select_from(LearningRecord)
            .join(Topic, Topic.id == LearningRecord.topic_id)
            .where(
                and_(
                    LearningRecord.user_id == user_id,
                    Topic.status == "published",
                    LearningRecord.status == "learning",
                )
            )
        )
        or 0
    )
    mastered_topics = (
        db.scalar(
            select(func.count())
            .select_from(LearningRecord)
            .join(Topic, Topic.id == LearningRecord.topic_id)
            .where(
                and_(
                    LearningRecord.user_id == user_id,
                    Topic.status == "published",
                    LearningRecord.status == "mastered",
                )
            )
        )
        or 0
    )
    return {
        "total_topics": total_topics,
        "started_topics": started_topics,
        "learning_topics": learning_topics,
        "mastered_topics": mastered_topics,
    }
