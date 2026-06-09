from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.learning_record import LearningRecord
from app.models.topic import Topic


DashboardTopicRow = tuple[Topic, LearningRecord | None]


def get_dashboard_topic_rows(db: Session, *, user_id: UUID) -> list[DashboardTopicRow]:
    statement = (
        select(Topic, LearningRecord)
        .outerjoin(
            LearningRecord,
            and_(
                LearningRecord.topic_id == Topic.id,
                LearningRecord.user_id == user_id,
            ),
        )
        .where(Topic.status == "published")
        .order_by(Topic.category.asc(), Topic.order_index.asc(), Topic.created_at.asc())
    )
    return list(db.execute(statement).all())
