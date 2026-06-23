from typing import Protocol

import httpx
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.judge import JudgeRequest, JudgeResponse


class JudgeClient(Protocol):
    async def judge(self, payload: JudgeRequest) -> JudgeResponse: ...


class HTTPJudgeClient:
    async def judge(self, payload: JudgeRequest) -> JudgeResponse:
        try:
            async with httpx.AsyncClient(timeout=settings.judge_request_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.judge_base_url.rstrip('/')}/internal/judge",
                    headers={"X-Judge-Token": settings.judge_internal_token},
                    json=payload.model_dump(mode="json"),
                )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail={"code": "JUDGE_TIMEOUT", "message": "Judge request timed out"},
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "JUDGE_UNAVAILABLE", "message": "Judge service is unavailable"},
            ) from exc

        if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={"code": "JUDGE_BUSY", "message": "Judge service is busy"},
            )
        if response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "JUDGE_UNAVAILABLE", "message": "Judge service is unavailable"},
            )
        if not response.is_success:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "JUDGE_UNAVAILABLE", "message": "Judge service is unavailable"},
            )
        try:
            return JudgeResponse.model_validate(response.json())
        except (ValueError, ValidationError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={"code": "JUDGE_INVALID_RESPONSE", "message": "Judge returned an invalid response"},
            ) from exc


def get_judge_client() -> JudgeClient:
    return HTTPJudgeClient()
