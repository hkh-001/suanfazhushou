from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import DataResponse, PaginatedResponse
from app.schemas.mistake_note import (
    MistakeNoteCreate,
    MistakeNoteDeleteResult,
    MistakeNoteDetail,
    MistakeNoteListItem,
    MistakeNoteUpdate,
)
from app.services.mistake_notes import (
    create_mistake_note,
    delete_mistake_note,
    get_mistake_note,
    list_mistake_notes,
    update_mistake_note,
)

router = APIRouter(prefix="/mistakes", tags=["mistakes"])


@router.post("", response_model=DataResponse[MistakeNoteDetail])
def create_mistake_note_endpoint(
    payload: MistakeNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[MistakeNoteDetail]:
    return DataResponse(data=create_mistake_note(db, user=current_user, payload=payload))


@router.get("", response_model=PaginatedResponse[MistakeNoteListItem])
def list_mistake_notes_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: Literal["open", "reviewing", "resolved"] | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[MistakeNoteListItem]:
    return list_mistake_notes(db, user=current_user, page=page, page_size=page_size, review_status=status)


@router.get("/{mistake_note_id}", response_model=DataResponse[MistakeNoteDetail])
def get_mistake_note_endpoint(
    mistake_note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[MistakeNoteDetail]:
    return DataResponse(data=get_mistake_note(db, user=current_user, mistake_note_id=mistake_note_id))


@router.put("/{mistake_note_id}", response_model=DataResponse[MistakeNoteDetail])
def update_mistake_note_endpoint(
    mistake_note_id: UUID,
    payload: MistakeNoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[MistakeNoteDetail]:
    return DataResponse(data=update_mistake_note(db, user=current_user, mistake_note_id=mistake_note_id, payload=payload))


@router.delete("/{mistake_note_id}", response_model=DataResponse[MistakeNoteDeleteResult])
def delete_mistake_note_endpoint(
    mistake_note_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[MistakeNoteDeleteResult]:
    return DataResponse(data=delete_mistake_note(db, user=current_user, mistake_note_id=mistake_note_id))
