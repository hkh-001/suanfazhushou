from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import DataResponse
from app.schemas.learning import LearningRecordRead, LearningRecordUpsert
from app.services.learning_records import save_learning_record

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post("/records", response_model=DataResponse[LearningRecordRead])
def upsert_learning_record(
    payload: LearningRecordUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DataResponse[LearningRecordRead]:
    return DataResponse(data=save_learning_record(db, user=current_user, payload=payload))
