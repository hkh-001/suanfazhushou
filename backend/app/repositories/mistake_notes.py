from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.mistake_note import MistakeNote


def count_user_mistake_notes(db: Session, *, user_id: UUID, review_status: str | None = None) -> int:
    stmt = select(func.count()).select_from(MistakeNote).where(MistakeNote.user_id == user_id)
    if review_status:
        stmt = stmt.where(MistakeNote.review_status == review_status)
    return db.scalar(stmt) or 0


def list_user_mistake_notes(
    db: Session,
    *,
    user_id: UUID,
    page: int,
    page_size: int,
    review_status: str | None = None,
) -> list[MistakeNote]:
    offset = (page - 1) * page_size
    stmt = (
        select(MistakeNote)
        .options(
            selectinload(MistakeNote.topic),
            selectinload(MistakeNote.problem),
            selectinload(MistakeNote.code_review),
        )
        .where(MistakeNote.user_id == user_id)
    )
    if review_status:
        stmt = stmt.where(MistakeNote.review_status == review_status)
    stmt = stmt.order_by(MistakeNote.created_at.desc(), MistakeNote.id.desc()).offset(offset).limit(page_size)
    return list(db.scalars(stmt).all())


def get_user_mistake_note(db: Session, *, mistake_note_id: UUID, user_id: UUID) -> MistakeNote | None:
    stmt = (
        select(MistakeNote)
        .options(
            selectinload(MistakeNote.topic),
            selectinload(MistakeNote.problem),
            selectinload(MistakeNote.code_review),
        )
        .where(MistakeNote.id == mistake_note_id, MistakeNote.user_id == user_id)
    )
    return db.scalar(stmt)


def create_mistake_note(db: Session, mistake_note: MistakeNote) -> MistakeNote:
    db.add(mistake_note)
    db.commit()
    db.refresh(mistake_note)
    return get_user_mistake_note(db, mistake_note_id=mistake_note.id, user_id=mistake_note.user_id) or mistake_note


def delete_mistake_note(db: Session, mistake_note: MistakeNote) -> None:
    db.delete(mistake_note)
    db.commit()
