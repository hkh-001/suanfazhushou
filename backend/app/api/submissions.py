from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_ai_provider, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.providers.ai.base import AIProvider
from app.schemas.common import DataResponse
from app.schemas.submission import SubmissionCreate, SubmissionDetail, SubmissionDiagnosisResponse
from app.services.judge.client import JudgeClient, get_judge_client
from app.services.submission_limiter import SubmissionLimiter, get_submission_limiter
from app.services.submissions import create_submission, diagnose_submission, get_submission

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=DataResponse[SubmissionDetail], status_code=status.HTTP_201_CREATED)
async def create_submission_endpoint(
    payload: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    judge_client: JudgeClient = Depends(get_judge_client),
    limiter: SubmissionLimiter = Depends(get_submission_limiter),
) -> DataResponse[SubmissionDetail]:
    return DataResponse(
        data=await create_submission(
            db,
            user=current_user,
            payload=payload,
            judge_client=judge_client,
            limiter=limiter,
        )
    )


@router.get("/{submission_id}", response_model=DataResponse[SubmissionDetail])
def get_submission_endpoint(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[SubmissionDetail]:
    return DataResponse(data=get_submission(db, user=current_user, submission_id=submission_id))


@router.post(
    "/{submission_id}/ai-diagnose",
    response_model=DataResponse[SubmissionDiagnosisResponse],
)
def diagnose_submission_endpoint(
    submission_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: AIProvider = Depends(get_ai_provider),
) -> DataResponse[SubmissionDiagnosisResponse]:
    return DataResponse(
        data=diagnose_submission(
            db,
            user=current_user,
            submission_id=submission_id,
            provider=provider,
        )
    )
