from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_ai_provider, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.providers.ai.base import AIProvider
from app.schemas.common import DataResponse
from app.schemas.ladder import LadderNodeDetail, LadderPracticeSubmitRequest, LadderPracticeSubmitResult, LadderSummary
from app.schemas.ladder_exam import (
    LadderExamAttemptDetail,
    LadderExamGenerationResult,
    LadderExamSubmitRequest,
    LadderExamSubmitResult,
)
from app.services.ladder import (
    complete_ladder_node_material,
    get_ladder_node,
    get_or_create_ladder,
    submit_ladder_node_practice,
)
from app.services.ladder_exams import generate_ladder_exam, get_ladder_exam, submit_ladder_exam

router = APIRouter(prefix="/ladder", tags=["ladder"])


@router.get("", response_model=DataResponse[LadderSummary])
def get_ladder_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LadderSummary]:
    return DataResponse(data=get_or_create_ladder(db, user=current_user))


@router.get("/nodes/{node_id}", response_model=DataResponse[LadderNodeDetail])
def get_ladder_node_endpoint(
    node_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LadderNodeDetail]:
    return DataResponse(data=get_ladder_node(db, user=current_user, node_id=node_id))


@router.post("/nodes/{node_id}/material-complete", response_model=DataResponse[LadderSummary])
def complete_ladder_node_material_endpoint(
    node_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LadderSummary]:
    return DataResponse(data=complete_ladder_node_material(db, user=current_user, node_id=node_id))


@router.post("/nodes/{node_id}/practice-submit", response_model=DataResponse[LadderPracticeSubmitResult])
def submit_ladder_node_practice_endpoint(
    node_id: UUID,
    payload: LadderPracticeSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LadderPracticeSubmitResult]:
    return DataResponse(data=submit_ladder_node_practice(db, user=current_user, node_id=node_id, payload=payload))


@router.post("/nodes/{node_id}/exam-generate", response_model=DataResponse[LadderExamGenerationResult])
def generate_ladder_exam_endpoint(
    node_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    provider: AIProvider = Depends(get_ai_provider),
) -> DataResponse[LadderExamGenerationResult]:
    return DataResponse(data=generate_ladder_exam(db, user=current_user, node_id=node_id, provider=provider))


@router.get("/exams/{attempt_id}", response_model=DataResponse[LadderExamAttemptDetail])
def get_ladder_exam_endpoint(
    attempt_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LadderExamAttemptDetail]:
    return DataResponse(data=get_ladder_exam(db, user=current_user, attempt_id=attempt_id))


@router.post("/exams/{attempt_id}/submit", response_model=DataResponse[LadderExamSubmitResult])
def submit_ladder_exam_endpoint(
    attempt_id: UUID,
    payload: LadderExamSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LadderExamSubmitResult]:
    return DataResponse(data=submit_ladder_exam(db, user=current_user, attempt_id=attempt_id, payload=payload))
