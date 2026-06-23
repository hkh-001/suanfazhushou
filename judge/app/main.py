import asyncio
import secrets
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Header, HTTPException, status

from app.config import settings
from app.docker_runner import DockerJudgeRunner
from app.limiter import ImmediateLimiter
from app.schemas import JudgeRequest, JudgeResponse

runner = DockerJudgeRunner()
limiter = ImmediateLimiter(settings.judge_max_concurrent)


async def _cleanup_loop() -> None:
    while True:
        await asyncio.to_thread(runner.cleanup_stale)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.to_thread(runner.cleanup_stale)
    cleanup_task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        cleanup_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleanup_task


app = FastAPI(title="AlgoMentor Judge", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/internal/judge", response_model=JudgeResponse)
async def judge(
    payload: JudgeRequest,
    x_judge_token: str = Header(default=""),
) -> JudgeResponse:
    expected = settings.judge_internal_token
    if not expected or not x_judge_token or not secrets.compare_digest(expected, x_judge_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    if not await limiter.try_acquire():
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Judge busy")
    try:
        return await runner.run_async(payload)
    finally:
        await limiter.release()
