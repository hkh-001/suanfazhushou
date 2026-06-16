from math import ceil
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.code_review import CodeReview
from app.models.problem import Problem
from app.models.topic import Topic
from app.models.user import User
from app.repositories.code_reviews import (
    count_user_code_reviews,
    create_code_review as insert_code_review,
    delete_code_review as remove_code_review,
    get_user_code_review,
    list_user_code_reviews,
)
from app.repositories.problems import get_user_problem
from app.repositories.topics import get_published_topic
from app.schemas.code_review import (
    CodeReviewCreate,
    CodeReviewDeleteResult,
    CodeReviewDetail,
    CodeReviewListItem,
    CodeReviewProblemRef,
    CodeReviewTopicRef,
)
from app.schemas.common import PaginatedResponse, Pagination

CODE_REVIEW_NOT_FOUND = {"code": "CODE_REVIEW_NOT_FOUND", "message": "Code review not found"}
PROBLEM_NOT_FOUND = {"code": "PROBLEM_NOT_FOUND", "message": "Problem not found"}
TOPIC_NOT_FOUND = {"code": "TOPIC_NOT_FOUND", "message": "Topic not found"}
LIST_ANALYSIS_SUMMARY_LENGTH = 200


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=CODE_REVIEW_NOT_FOUND)


def _topic_ref(topic: Topic | None) -> CodeReviewTopicRef | None:
    if topic is None:
        return None
    return CodeReviewTopicRef(id=topic.id, title=topic.title, slug=topic.slug, category=topic.category)


def _problem_ref(problem: Problem | None) -> CodeReviewProblemRef | None:
    if problem is None:
        return None
    return CodeReviewProblemRef(id=problem.id, display_id=problem.display_id, title=problem.title)


def _analysis_summary(analysis_result: str) -> str:
    if len(analysis_result) <= LIST_ANALYSIS_SUMMARY_LENGTH:
        return analysis_result
    return f"{analysis_result[:LIST_ANALYSIS_SUMMARY_LENGTH]}..."


def _to_list_item(code_review: CodeReview, *, full_analysis: bool = False) -> CodeReviewListItem:
    return CodeReviewListItem(
        id=code_review.id,
        topic_id=code_review.topic_id,
        problem_id=code_review.problem_id,
        language=code_review.language,
        question=code_review.question,
        analysis_result=code_review.analysis_result if full_analysis else _analysis_summary(code_review.analysis_result),
        model=code_review.model,
        prompt_type=code_review.prompt_type,
        input_tokens=code_review.input_tokens,
        output_tokens=code_review.output_tokens,
        topic=_topic_ref(code_review.topic),
        problem=_problem_ref(code_review.problem),
        created_at=code_review.created_at,
        updated_at=code_review.updated_at,
    )


def _to_detail(code_review: CodeReview) -> CodeReviewDetail:
    return CodeReviewDetail(**_to_list_item(code_review, full_analysis=True).model_dump(), code=code_review.code)


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


def create_code_review(db: Session, *, user: User, payload: CodeReviewCreate) -> CodeReviewDetail:
    _ensure_topic(db, payload.topic_id)
    _ensure_problem(db, problem_id=payload.problem_id, user_id=user.id)
    code_review = CodeReview(
        user_id=user.id,
        topic_id=payload.topic_id,
        problem_id=payload.problem_id,
        language=payload.language,
        question=payload.question,
        code=payload.code,
        analysis_result=payload.analysis_result,
        model=payload.model,
        prompt_type=payload.prompt_type,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
    )
    return _to_detail(insert_code_review(db, code_review))


def list_code_reviews(db: Session, *, user: User, page: int, page_size: int) -> PaginatedResponse[CodeReviewListItem]:
    total = count_user_code_reviews(db, user_id=user.id)
    items = list_user_code_reviews(db, user_id=user.id, page=page, page_size=page_size)
    return PaginatedResponse(
        data=[_to_list_item(item) for item in items],
        pagination=Pagination(page=page, page_size=page_size, total=total, total_pages=ceil(total / page_size) if total else 0),
    )


def get_code_review(db: Session, *, user: User, code_review_id: UUID) -> CodeReviewDetail:
    code_review = get_user_code_review(db, code_review_id=code_review_id, user_id=user.id)
    if code_review is None:
        raise _not_found()
    return _to_detail(code_review)


def delete_code_review(db: Session, *, user: User, code_review_id: UUID) -> CodeReviewDeleteResult:
    code_review = get_user_code_review(db, code_review_id=code_review_id, user_id=user.id)
    if code_review is None:
        raise _not_found()
    remove_code_review(db, code_review)
    return CodeReviewDeleteResult(success=True)
