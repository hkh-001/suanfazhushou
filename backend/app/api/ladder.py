from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import DataResponse
from app.schemas.ladder import LadderNodeDetail, LadderSummary
from app.services.ladder import complete_ladder_node_material, get_ladder_node, get_or_create_ladder

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
