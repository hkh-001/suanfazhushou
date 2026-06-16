from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.code_review import CodeReviewCreate, CodeReviewDeleteResult, CodeReviewDetail, CodeReviewListItem
from app.schemas.common import DataResponse, PaginatedResponse
from app.services.code_reviews import create_code_review, delete_code_review, get_code_review, list_code_reviews

router = APIRouter(prefix="/code-reviews", tags=["code-reviews"])


@router.post("", response_model=DataResponse[CodeReviewDetail])
def create_code_review_endpoint(
    payload: CodeReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[CodeReviewDetail]:
    return DataResponse(data=create_code_review(db, user=current_user, payload=payload))


@router.get("", response_model=PaginatedResponse[CodeReviewListItem])
def list_code_reviews_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[CodeReviewListItem]:
    return list_code_reviews(db, user=current_user, page=page, page_size=page_size)


@router.get("/{code_review_id}", response_model=DataResponse[CodeReviewDetail])
def get_code_review_endpoint(
    code_review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[CodeReviewDetail]:
    return DataResponse(data=get_code_review(db, user=current_user, code_review_id=code_review_id))


@router.delete("/{code_review_id}", response_model=DataResponse[CodeReviewDeleteResult])
def delete_code_review_endpoint(
    code_review_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[CodeReviewDeleteResult]:
    return DataResponse(data=delete_code_review(db, user=current_user, code_review_id=code_review_id))
