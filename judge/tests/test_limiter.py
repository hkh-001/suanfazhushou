import asyncio

from app.limiter import ImmediateLimiter


def test_limiter_rejects_without_waiting() -> None:
    async def run() -> None:
        limiter = ImmediateLimiter(1)
        assert await limiter.try_acquire() is True
        assert await limiter.try_acquire() is False
        await limiter.release()
        assert await limiter.try_acquire() is True

    asyncio.run(run())
