from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthData, HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(
        data=HealthData(
            status="ok",
            service="backend",
            app_name=settings.app_name,
            environment=settings.app_env,
        )
    )
