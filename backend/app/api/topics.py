from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import DataResponse, PaginatedResponse
from app.schemas.interactive_lesson import InteractiveLessonDetail
from app.schemas.topic import TopicDetail, TopicListItem
from app.services.interactive_lessons import create_topic_interactive_lesson
from app.services.topics import get_topic, list_topics

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=PaginatedResponse[TopicListItem])
def get_topics(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[TopicListItem]:
    return list_topics(db, user_id=current_user.id, page=page, page_size=page_size)


@router.post("/{topic_id}/interactive-lessons", response_model=DataResponse[InteractiveLessonDetail])
async def generate_topic_interactive_lesson(
    topic_id: UUID,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[InteractiveLessonDetail]:
    return DataResponse(data=await create_topic_interactive_lesson(db, topic_id=topic_id, user=current_user, force=force))


@router.get("/{topic_id}", response_model=DataResponse[TopicDetail])
def get_topic_detail(
    topic_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[TopicDetail]:
    return DataResponse(data=get_topic(db, topic_id=topic_id, user_id=current_user.id))
