from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai import AIResponseData, ChatRequest, CodeReviewRequest, ProblemGenerationRequest
from app.schemas.common import DataResponse
from app.services.ai.service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=DataResponse[AIResponseData])
def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[AIResponseData]:
    return DataResponse(data=AIService(db).chat(user=current_user, payload=payload))


@router.post("/code-review", response_model=DataResponse[AIResponseData])
def code_review(
    payload: CodeReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[AIResponseData]:
    return DataResponse(data=AIService(db).code_review(user=current_user, payload=payload))


@router.post("/generate-problem", response_model=DataResponse[AIResponseData])
def generate_problem(
    payload: ProblemGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[AIResponseData]:
    return DataResponse(data=AIService(db).generate_problem(user=current_user, payload=payload))
