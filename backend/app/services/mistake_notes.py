from datetime import datetime, timezone
from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.mistake_note import MistakeNote
from app.models.user import User
from app.repositories.code_reviews import get_user_code_review
from app.repositories.mistake_notes import (
    count_user_mistake_notes,
    create_mistake_note as insert_mistake_note,
    delete_mistake_note as remove_mistake_note,
    get_user_mistake_note,
    list_user_mistake_notes,
)
from app.repositories.problems import get_user_problem
from app.repositories.topics import get_published_topic
from app.schemas.code_review import CodeReviewProblemRef, CodeReviewTopicRef
from app.schemas.common import PaginatedResponse, Pagination
from app.schemas.mistake_note import (
    MistakeCodeReviewRef,
    MistakeNoteCreate,
    MistakeNoteDeleteResult,
    MistakeNoteDetail,
    MistakeNoteListItem,
    MistakeNoteUpdate,
)

MISTAKE_NOTE_NOT_FOUND = {"code": "MISTAKE_NOTE_NOT_FOUND", "message": "Mistake note not found"}
CODE_REVIEW_NOT_FOUND = {"code": "CODE_REVIEW_NOT_FOUND", "message": "Code review not found"}
PROBLEM_NOT_FOUND = {"code": "PROBLEM_NOT_FOUND", "message": "Problem not found"}
TOPIC_NOT_FOUND = {"code": "TOPIC_NOT_FOUND", "message": "Topic not found"}
VALIDATION_ERROR = {"code": "VALIDATION_ERROR", "message": "Request validation failed"}


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=MISTAKE_NOTE_NOT_FOUND)


def _validation_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=VALIDATION_ERROR)


def _ensure_topic(db: Session, topic_id: UUID | None) -> None:
    if topic_id is None:
        return
    if get_published_topic(db, topic_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TOPIC_NOT_FOUND)


def _ensure_problem(db: Session, *, problem_id: UUID | None, user_id: UUID) -> None:
    if problem_id is None:
        return
    if get_user_problem(db, problem_id=problem_id, user_id=user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROBLEM_NOT_FOUND)


def _ensure_code_review(db: Session, *, code_review_id: UUID | None, user_id: UUID) -> None:
    if code_review_id is None:
        return
    if get_user_code_review(db, code_review_id=code_review_id, user_id=user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CODE_REVIEW_NOT_FOUND)


def _problem_ref(note: MistakeNote) -> CodeReviewProblemRef | None:
    if note.problem is None:
        return None
    return CodeReviewProblemRef(id=note.problem.id, display_id=note.problem.display_id, title=note.problem.title)


def _topic_ref(note: MistakeNote) -> CodeReviewTopicRef | None:
    if note.topic is None:
        return None
    return CodeReviewTopicRef(id=note.topic.id, title=note.topic.title, slug=note.topic.slug, category=note.topic.category)


def _code_review_ref(note: MistakeNote) -> MistakeCodeReviewRef | None:
    if note.code_review is None:
        return None
    return MistakeCodeReviewRef(
        id=note.code_review.id,
        language=note.code_review.language,
        question=note.code_review.question,
        created_at=note.code_review.created_at,
    )


def _to_list_item(note: MistakeNote) -> MistakeNoteListItem:
    return MistakeNoteListItem(
        id=note.id,
        problem_id=note.problem_id,
        topic_id=note.topic_id,
        code_review_id=note.code_review_id,
        title=note.title,
        error_type=note.error_type,
        root_cause=note.root_cause,
        review_status=note.review_status,
        resolved_at=note.resolved_at,
        problem=_problem_ref(note),
        topic=_topic_ref(note),
        code_review=_code_review_ref(note),
        created_at=note.created_at,
        updated_at=note.updated_at,
    )


def _to_detail(note: MistakeNote) -> MistakeNoteDetail:
    return MistakeNoteDetail(
        **_to_list_item(note).model_dump(),
        wrong_code=note.wrong_code,
        fixed_code=note.fixed_code,
        fix_suggestion=note.fix_suggestion,
        ai_summary=note.ai_summary,
        user_reflection=note.user_reflection,
    )


def create_mistake_note(db: Session, *, user: User, payload: MistakeNoteCreate) -> MistakeNoteDetail:
    _ensure_topic(db, payload.topic_id)
    _ensure_problem(db, problem_id=payload.problem_id, user_id=user.id)
    _ensure_code_review(db, code_review_id=payload.code_review_id, user_id=user.id)
    note = MistakeNote(
        user_id=user.id,
        problem_id=payload.problem_id,
        topic_id=payload.topic_id,
        code_review_id=payload.code_review_id,
        title=payload.title,
        error_type=payload.error_type,
        root_cause=payload.root_cause,
        wrong_code=payload.wrong_code,
        fixed_code=payload.fixed_code,
        fix_suggestion=payload.fix_suggestion,
        ai_summary=payload.ai_summary,
        user_reflection=payload.user_reflection,
        review_status=payload.review_status,
        resolved_at=datetime.now(timezone.utc) if payload.review_status == "resolved" else None,
    )
    return _to_detail(insert_mistake_note(db, note))


def list_mistake_notes(
    db: Session,
    *,
    user: User,
    page: int,
    page_size: int,
    review_status: str | None = None,
) -> PaginatedResponse[MistakeNoteListItem]:
    total = count_user_mistake_notes(db, user_id=user.id, review_status=review_status)
    items = list_user_mistake_notes(
        db,
        user_id=user.id,
        page=page,
        page_size=page_size,
        review_status=review_status,
    )
    return PaginatedResponse(
        data=[_to_list_item(item) for item in items],
        pagination=Pagination(page=page, page_size=page_size, total=total, total_pages=ceil(total / page_size) if total else 0),
    )


def get_mistake_note(db: Session, *, user: User, mistake_note_id: UUID) -> MistakeNoteDetail:
    note = get_user_mistake_note(db, mistake_note_id=mistake_note_id, user_id=user.id)
    if note is None:
        raise _not_found()
    return _to_detail(note)


def update_mistake_note(db: Session, *, user: User, mistake_note_id: UUID, payload: MistakeNoteUpdate) -> MistakeNoteDetail:
    note = get_user_mistake_note(db, mistake_note_id=mistake_note_id, user_id=user.id)
    if note is None:
        raise _not_found()

    fields = payload.model_fields_set
    for required_field in ("title", "root_cause"):
        if required_field in fields and getattr(payload, required_field) is None:
            raise _validation_error()

    if "topic_id" in fields:
        _ensure_topic(db, payload.topic_id)
        note.topic_id = payload.topic_id
    if "problem_id" in fields:
        _ensure_problem(db, problem_id=payload.problem_id, user_id=user.id)
        note.problem_id = payload.problem_id
    if "code_review_id" in fields:
        _ensure_code_review(db, code_review_id=payload.code_review_id, user_id=user.id)
        note.code_review_id = payload.code_review_id

    for field in (
        "title",
        "error_type",
        "root_cause",
        "wrong_code",
        "fixed_code",
        "fix_suggestion",
        "ai_summary",
        "user_reflection",
    ):
        if field in fields:
            setattr(note, field, getattr(payload, field))

    if "review_status" in fields:
        if payload.review_status is None:
            raise _validation_error()
        previous_status = note.review_status
        note.review_status = payload.review_status
        if payload.review_status == "resolved" and previous_status != "resolved":
            note.resolved_at = datetime.now(timezone.utc)
        elif payload.review_status != "resolved":
            note.resolved_at = None

    db.commit()
    refreshed = get_user_mistake_note(db, mistake_note_id=note.id, user_id=user.id)
    if refreshed is None:
        raise _not_found()
    return _to_detail(refreshed)


def delete_mistake_note(db: Session, *, user: User, mistake_note_id: UUID) -> MistakeNoteDeleteResult:
    note = get_user_mistake_note(db, mistake_note_id=mistake_note_id, user_id=user.id)
    if note is None:
        raise _not_found()
    remove_mistake_note(db, note)
    return MistakeNoteDeleteResult(success=True)
