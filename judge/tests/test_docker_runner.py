import asyncio
import threading
import time
from uuid import uuid4

import pytest

from app.config import settings
from app.docker_runner import DockerJudgeRunner
from app.schemas import JudgeRequest, TestCaseRequest as JudgeTestCaseRequest


class FakeContainers:
    def list(self, **kwargs):
        return []


class FakeDockerClient:
    containers = FakeContainers()


def _payload() -> JudgeRequest:
    return JudgeRequest(
        submission_id=uuid4(),
        language="python",
        source_code="print(1)",
        test_cases=[
            JudgeTestCaseRequest(
                id=uuid4(),
                case_index=1,
                name="sample",
                input_text="",
                expected_output_text="1\n",
                is_sample=True,
            )
        ],
    )


def test_container_security_configuration() -> None:
    runner = DockerJudgeRunner(client=FakeDockerClient())
    config = runner._container_config(_payload())

    assert config["network_disabled"] is True
    assert config["read_only"] is True
    assert config["pids_limit"] == 128
    assert config["cap_drop"] == ["ALL"]
    assert config["security_opt"] == ["no-new-privileges:true"]
    assert config["user"] == "10001:10001"
    assert "/workspace" in config["tmpfs"]
    assert "size=64m" in config["tmpfs"]["/workspace"]
    assert "exec" in config["tmpfs"]["/workspace"]
    assert "volumes" not in config


def test_cancelled_request_waits_for_runner_cleanup(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run() -> None:
        runner = DockerJudgeRunner(client=FakeDockerClient())
        completed = threading.Event()

        def slow_run(payload):
            time.sleep(0.05)
            completed.set()
            return None

        monkeypatch.setattr(runner, "run", slow_run)
        task = asyncio.create_task(runner.run_async(_payload()))
        await asyncio.sleep(0.01)
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task
        assert completed.is_set()

    asyncio.run(run())


def test_hard_timeout_returns_without_waiting_for_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        runner = DockerJudgeRunner(client=FakeDockerClient())
        completed = threading.Event()

        def stuck_run(payload):
            time.sleep(0.1)
            completed.set()
            return None

        monkeypatch.setattr(runner, "run", stuck_run)
        monkeypatch.setattr(settings, "judge_request_hard_timeout_seconds", 0.01)
        started = time.monotonic()

        result = await runner.run_async(_payload())

        assert time.monotonic() - started < 0.05
        assert result.verdict == "internal_error"
        assert result.error_message == "Judge execution deadline exceeded"
        assert completed.is_set() is False
        await asyncio.sleep(0.12)
        assert completed.is_set() is True

    asyncio.run(run())
