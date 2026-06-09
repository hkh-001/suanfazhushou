from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.topics import (
    count_published_topics,
    get_published_topic_with_learning,
    list_published_topics_with_learning,
)
from app.schemas.common import PaginatedResponse, Pagination
from app.schemas.topic import LearningStatus, TopicDetail, TopicListItem


def _learning_status(record) -> LearningStatus:
    if record is None:
        return LearningStatus()
    return LearningStatus(
        status=record.status,
        progress_percent=record.progress_percent,
        mastery_level=record.mastery_level,
        review_count=record.review_count,
        last_studied_at=record.last_studied_at,
        next_review_at=record.next_review_at,
        note=record.note,
    )


def _topic_list_item(topic, record) -> TopicListItem:
    return TopicListItem(
        id=topic.id,
        title=topic.title,
        slug=topic.slug,
        category=topic.category,
        level=topic.level,
        difficulty_score=topic.difficulty_score,
        summary=topic.summary,
        estimated_minutes=topic.estimated_minutes,
        order_index=topic.order_index,
        learning_status=_learning_status(record),
    )


def list_topics(db: Session, *, user_id: UUID, page: int, page_size: int) -> PaginatedResponse[TopicListItem]:
    total = count_published_topics(db)
    rows = list_published_topics_with_learning(db, user_id=user_id, page=page, page_size=page_size)
    return PaginatedResponse(
        data=[_topic_list_item(topic, record) for topic, record in rows],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        ),
    )


def get_topic(db: Session, *, topic_id: UUID, user_id: UUID) -> TopicDetail:
    row = get_published_topic_with_learning(db, topic_id=topic_id, user_id=user_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TOPIC_NOT_FOUND", "message": "Topic not found"},
        )
    topic, record = row
    return TopicDetail(
        **_topic_list_item(topic, record).model_dump(),
        content_markdown=topic.content_markdown,
        template_code_cpp=topic.template_code_cpp,
        template_code_python=topic.template_code_python,
        complexity_note=topic.complexity_note,
        common_pitfalls=topic.common_pitfalls,
        published_at=topic.published_at,
    )
