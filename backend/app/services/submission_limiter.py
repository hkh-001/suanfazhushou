import asyncio

from fastapi import HTTPException, status

from app.core.config import settings


class SubmissionLimiter:
    def __init__(self, limit: int) -> None:
        self._limit = max(1, limit)
        self._active = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            if self._active >= self._limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"code": "JUDGE_BUSY", "message": "Judge service is busy"},
                )
            self._active += 1

    async def release(self) -> None:
        async with self._lock:
            self._active = max(0, self._active - 1)


# Process-local only; the Judge service limiter is the cross-worker safety backstop.
submission_limiter = SubmissionLimiter(settings.submission_max_in_flight)


def get_submission_limiter() -> SubmissionLimiter:
    return submission_limiter
