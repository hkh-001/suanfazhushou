from uuid import UUID

from sqlalchemy.orm import Session

from app.models.learning_record import LearningRecord
from app.models.topic import Topic
from app.repositories.dashboard import get_dashboard_topic_rows
from app.schemas.dashboard import (
    DashboardActivityItem,
    DashboardCategoryProgress,
    DashboardNextStep,
    DashboardReviewItem,
    DashboardStatusCount,
    DashboardSummary,
)


def _percent(count: int, total: int) -> int:
    return round((count / total) * 100) if total else 0


def _is_started(record: LearningRecord | None) -> bool:
    return record is not None and record.status in {"learning", "mastered"}


def _is_mastered(record: LearningRecord | None) -> bool:
    return record is not None and record.status == "mastered"


def _is_learning(record: LearningRecord | None) -> bool:
    return record is not None and record.status == "learning"


def _activity_item(topic: Topic, record: LearningRecord) -> DashboardActivityItem:
    return DashboardActivityItem(
        topic_id=topic.id,
        title=topic.title,
        category=topic.category,
        status=record.status,
        progress_percent=record.progress_percent,
        mastery_level=record.mastery_level,
        review_count=record.review_count,
        last_studied_at=record.last_studied_at,
    )


def _review_reason(record: LearningRecord) -> str:
    if record.status == "learning":
        return "Learning topic needs another review"
    return "Continue reviewing to reach mastery"


def get_summary(db: Session, *, user_id: UUID) -> DashboardSummary:
    rows = get_dashboard_topic_rows(db, user_id=user_id)
    total = len(rows)
    learning = sum(1 for _, record in rows if _is_learning(record))
    mastered = sum(1 for _, record in rows if _is_mastered(record))
    started = sum(1 for _, record in rows if _is_started(record))
    not_started = total - started
    total_estimated_minutes = sum(topic.estimated_minutes for topic, _ in rows)
    completed_estimated_minutes = sum(topic.estimated_minutes for topic, record in rows if _is_mastered(record))

    status_counts = [
        DashboardStatusCount(
            status="not_started",
            label="Not started",
            count=not_started,
            percent=_percent(not_started, total),
        ),
        DashboardStatusCount(
            status="learning",
            label="Learning",
            count=learning,
            percent=_percent(learning, total),
        ),
        DashboardStatusCount(
            status="mastered",
            label="Mastered",
            count=mastered,
            percent=_percent(mastered, total),
        ),
    ]

    category_progress: list[DashboardCategoryProgress] = []
    categories = sorted({topic.category for topic, _ in rows})
    for category in categories:
        category_rows = [(topic, record) for topic, record in rows if topic.category == category]
        category_total = len(category_rows)
        category_started = sum(1 for _, record in category_rows if _is_started(record))
        category_mastered = sum(1 for _, record in category_rows if _is_mastered(record))
        category_estimated = sum(topic.estimated_minutes for topic, _ in category_rows)
        category_completed = sum(
            topic.estimated_minutes for topic, record in category_rows if _is_mastered(record)
        )
        category_progress.append(
            DashboardCategoryProgress(
                category=category,
                total_topics=category_total,
                started_topics=category_started,
                mastered_topics=category_mastered,
                progress_percent=_percent(category_mastered, category_total),
                estimated_minutes=category_estimated,
                completed_estimated_minutes=category_completed,
            )
        )

    records = [(topic, record) for topic, record in rows if record is not None]
    recent_activity = [
        _activity_item(topic, record)
        for topic, record in sorted(records, key=lambda item: item[1].last_studied_at, reverse=True)[:5]
    ]

    review_candidates = [
        (topic, record)
        for topic, record in records
        if record.status != "mastered" and record.status != "not_started" and record.mastery_level < 5
    ]
    review_candidates.sort(
        key=lambda item: (
            0 if item[1].status == "learning" else 1,
            item[1].next_review_at is None,
            item[1].next_review_at,
            item[1].mastery_level,
            item[1].last_studied_at,
        )
    )
    review_queue = [
        DashboardReviewItem(
            **_activity_item(topic, record).model_dump(),
            next_review_at=record.next_review_at,
            reason=_review_reason(record),
        )
        for topic, record in review_candidates[:5]
    ]

    unstarted_topics = [topic for topic, record in rows if record is None]
    unstarted_topics.sort(key=lambda topic: (topic.order_index, topic.difficulty_score, topic.created_at))
    if unstarted_topics:
        next_steps = [
            DashboardNextStep(
                topic_id=topic.id,
                title=topic.title,
                category=topic.category,
                level=topic.level,
                difficulty_score=topic.difficulty_score,
                estimated_minutes=topic.estimated_minutes,
                reason="Next published topic with no learning record",
                rank=index,
            )
            for index, topic in enumerate(unstarted_topics[:3], start=1)
        ]
    else:
        non_mastered = [(topic, record) for topic, record in records if record.status != "mastered"]
        non_mastered.sort(key=lambda item: (item[1].mastery_level, item[1].last_studied_at))
        next_steps = [
            DashboardNextStep(
                topic_id=topic.id,
                title=topic.title,
                category=topic.category,
                level=topic.level,
                difficulty_score=topic.difficulty_score,
                estimated_minutes=topic.estimated_minutes,
                reason="Continue a topic that is not mastered yet",
                rank=index,
            )
            for index, (topic, record) in enumerate(non_mastered[:3], start=1)
        ]

    return DashboardSummary(
        total_topics=total,
        started_topics=started,
        mastered_topics=mastered,
        learning_topics=learning,
        progress_percent=_percent(mastered, total),
        not_started_topics=not_started,
        total_estimated_minutes=total_estimated_minutes,
        completed_estimated_minutes=completed_estimated_minutes,
        status_counts=status_counts,
        category_progress=category_progress,
        recent_activity=recent_activity,
        review_queue=review_queue,
        next_steps=next_steps,
    )
