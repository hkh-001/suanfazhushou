from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import DataResponse
from app.schemas.interactive_lesson import InteractiveLessonDetail
from app.services.interactive_lessons import get_interactive_lesson, refresh_interactive_lesson

router = APIRouter(prefix="/interactive-lessons", tags=["interactive-lessons"])


@router.get("/{lesson_id}", response_model=DataResponse[InteractiveLessonDetail])
def get_interactive_lesson_detail(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[InteractiveLessonDetail]:
    return DataResponse(data=get_interactive_lesson(db, lesson_id=lesson_id, user=current_user))


@router.post("/{lesson_id}/refresh", response_model=DataResponse[InteractiveLessonDetail])
async def refresh_interactive_lesson_status(
    lesson_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[InteractiveLessonDetail]:
    return DataResponse(data=await refresh_interactive_lesson(db, lesson_id=lesson_id, user=current_user))
