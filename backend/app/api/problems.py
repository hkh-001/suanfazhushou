from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import DataResponse, PaginatedResponse
from app.schemas.problem import (
    GeneratedProblemSaveRequest,
    ProblemCreate,
    ProblemDeleteResult,
    ProblemDetail,
    ProblemListItem,
    ProblemUpdate,
)
from app.schemas.problem_import import ProblemImportResult
from app.services.problem_imports import ZIP_MAX_BYTES, import_problem_zip
from app.services.problems import (
    create_problem,
    delete_problem,
    get_problem,
    get_public_problem,
    list_problems,
    list_public_problem_bank,
    save_ai_generated_problem,
    update_problem,
)

router = APIRouter(prefix="/problems", tags=["problems"])


@router.post("", response_model=DataResponse[ProblemDetail])
def create_problem_endpoint(
    payload: ProblemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemDetail]:
    return DataResponse(data=create_problem(db, user=current_user, payload=payload))


@router.get("", response_model=PaginatedResponse[ProblemListItem])
def list_problems_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ProblemListItem]:
    return list_problems(db, user=current_user, page=page, page_size=page_size)


@router.post("/save-ai-generated", response_model=DataResponse[ProblemDetail])
def save_ai_generated_problem_endpoint(
    payload: GeneratedProblemSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemDetail]:
    return DataResponse(data=save_ai_generated_problem(db, user=current_user, payload=payload))


@router.post("/import/zip", response_model=DataResponse[ProblemImportResult], status_code=status.HTTP_201_CREATED)
async def import_problem_zip_endpoint(
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemImportResult]:
    if file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "ZIP_FILE_REQUIRED", "message": "ZIP file is required"},
        )
    content = await file.read(ZIP_MAX_BYTES + 1)
    return DataResponse(data=import_problem_zip(db, user=current_user, zip_bytes=content))


@router.get("/public", response_model=PaginatedResponse[ProblemListItem])
def list_public_problems_endpoint(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PaginatedResponse[ProblemListItem]:
    return list_public_problem_bank(db, user=current_user, page=page, page_size=page_size)


@router.get("/public/{problem_id}", response_model=DataResponse[ProblemDetail])
def get_public_problem_endpoint(
    problem_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemDetail]:
    return DataResponse(data=get_public_problem(db, user=current_user, problem_id=problem_id))


@router.get("/{problem_id}", response_model=DataResponse[ProblemDetail])
def get_problem_endpoint(
    problem_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemDetail]:
    return DataResponse(data=get_problem(db, user=current_user, problem_id=problem_id))


@router.put("/{problem_id}", response_model=DataResponse[ProblemDetail])
def update_problem_endpoint(
    problem_id: UUID,
    payload: ProblemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemDetail]:
    return DataResponse(data=update_problem(db, user=current_user, problem_id=problem_id, payload=payload))


@router.delete("/{problem_id}", response_model=DataResponse[ProblemDeleteResult])
def delete_problem_endpoint(
    problem_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[ProblemDeleteResult]:
    return DataResponse(data=delete_problem(db, user=current_user, problem_id=problem_id))
