from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.code_review import CodeReview


def count_user_code_reviews(db: Session, *, user_id: UUID) -> int:
    return db.scalar(select(func.count()).select_from(CodeReview).where(CodeReview.user_id == user_id)) or 0


def list_user_code_reviews(db: Session, *, user_id: UUID, page: int, page_size: int) -> list[CodeReview]:
    offset = (page - 1) * page_size
    stmt = (
        select(CodeReview)
        .options(selectinload(CodeReview.topic), selectinload(CodeReview.problem))
        .where(CodeReview.user_id == user_id)
        .order_by(CodeReview.created_at.desc(), CodeReview.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(db.scalars(stmt).all())


def get_user_code_review(db: Session, *, code_review_id: UUID, user_id: UUID) -> CodeReview | None:
    stmt = (
        select(CodeReview)
        .options(selectinload(CodeReview.topic), selectinload(CodeReview.problem))
        .where(CodeReview.id == code_review_id, CodeReview.user_id == user_id)
    )
    return db.scalar(stmt)


def create_code_review(db: Session, code_review: CodeReview) -> CodeReview:
    db.add(code_review)
    db.commit()
    db.refresh(code_review)
    return get_user_code_review(db, code_review_id=code_review.id, user_id=code_review.user_id) or code_review


def delete_code_review(db: Session, code_review: CodeReview) -> None:
    db.delete(code_review)
    db.commit()
