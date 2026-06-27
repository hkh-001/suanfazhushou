from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import DataResponse
from app.schemas.openmaic import (
    OpenMAICGeneratePayload,
    OpenMAICJobStatus,
    OpenMAICPocGenerateRequest,
    OpenMAICPocStatus,
)
from app.services.openmaic import HttpOpenMAICClient, OpenMAICClient, OpenMAICClientError
from app.services.openmaic.client import sanitize_openmaic_base_url

router = APIRouter(prefix="/openmaic/poc", tags=["openmaic"])


def get_openmaic_client() -> OpenMAICClient:
    return HttpOpenMAICClient()


def _feature_guard() -> None:
    if not settings.enable_openmaic_integration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FEATURE_DISABLED", "message": "OpenMAIC integration is disabled"},
        )


def _admin_guard(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "ADMIN_REQUIRED", "message": "Admin role is required"},
        )


def _configured_base_url() -> str | None:
    try:
        return sanitize_openmaic_base_url(settings.openmaic_base_url)
    except OpenMAICClientError:
        return None


def _auth_configured() -> bool:
    mode = settings.openmaic_auth_mode.strip().lower() or "none"
    if mode == "none":
        return False
    if mode == "header":
        return bool(settings.openmaic_auth_header_name.strip() and settings.openmaic_auth_header_value)
    if mode == "query":
        return bool(settings.openmaic_auth_query_name.strip() and settings.openmaic_auth_query_value)
    if mode == "body":
        return bool(settings.openmaic_auth_body_field.strip() and settings.openmaic_auth_body_value)
    return False


def _handle_openmaic_error(exc: OpenMAICClientError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    )


def _build_requirement(payload: OpenMAICPocGenerateRequest) -> str:
    goal = payload.goal.strip() if payload.goal else "算法学习能力提升"
    requirement = f"""请生成一节中文互动算法课堂。

主题：{payload.title.strip()}
学习者水平：{payload.audience_level.strip()}
学习目标：{goal}
内容摘要：{payload.summary.strip()}

课堂要求：
1. 使用中文讲解，先解释概念，再给推导过程。
2. 包含 AI 老师讲解、AI 同学常见疑问、课堂测验和可视化/模拟建议。
3. 面向算法学习场景，避免泛泛而谈。
4. 不要求运行代码，不生成需要外部判题的任务。
5. 不包含任何敏感个人信息。
"""
    return requirement[:2000]


@router.get("/status", response_model=DataResponse[OpenMAICPocStatus])
def get_openmaic_poc_status(
    current_user: User = Depends(get_current_user),
) -> DataResponse[OpenMAICPocStatus]:
    _feature_guard()
    _admin_guard(current_user)
    base_url = _configured_base_url()
    return DataResponse(
        data=OpenMAICPocStatus(
            enabled=settings.enable_openmaic_integration,
            configured=base_url is not None,
            base_url=base_url,
            generate_path=settings.openmaic_generate_path,
            auth_configured=_auth_configured(),
            auth_mode=settings.openmaic_auth_mode.strip().lower() or "none",
        )
    )


@router.post("/generate", response_model=DataResponse[OpenMAICJobStatus])
async def generate_openmaic_classroom(
    payload: OpenMAICPocGenerateRequest,
    current_user: User = Depends(get_current_user),
) -> DataResponse[OpenMAICJobStatus]:
    _feature_guard()
    _admin_guard(current_user)
    try:
        client = get_openmaic_client()
        result = await client.generate_classroom(
            OpenMAICGeneratePayload(requirement=_build_requirement(payload))
        )
    except OpenMAICClientError as exc:
        raise _handle_openmaic_error(exc) from exc
    return DataResponse(data=result)


@router.get("/jobs/{job_id}", response_model=DataResponse[OpenMAICJobStatus])
async def get_openmaic_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
) -> DataResponse[OpenMAICJobStatus]:
    _feature_guard()
    _admin_guard(current_user)
    try:
        client = get_openmaic_client()
        result = await client.get_job(job_id)
    except OpenMAICClientError as exc:
        raise _handle_openmaic_error(exc) from exc
    return DataResponse(data=result)
