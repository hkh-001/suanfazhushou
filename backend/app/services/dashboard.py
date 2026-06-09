from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.dashboard import get_dashboard_counts
from app.schemas.dashboard import DashboardSummary


def get_summary(db: Session, *, user_id: UUID) -> DashboardSummary:
    counts = get_dashboard_counts(db, user_id=user_id)
    total = counts["total_topics"]
    mastered = counts["mastered_topics"]
    return DashboardSummary(
        total_topics=total,
        started_topics=counts["started_topics"],
        mastered_topics=mastered,
        learning_topics=counts["learning_topics"],
        progress_percent=round((mastered / total) * 100) if total else 0,
    )
