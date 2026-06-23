import os
from uuid import uuid4

import docker
import pytest

from app.config import settings
from app.docker_runner import DockerJudgeRunner
from app.schemas import JudgeRequest, TestCaseRequest as JudgeTestCaseRequest


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_JUDGE_DOCKER_TESTS") != "1",
    reason="Set RUN_JUDGE_DOCKER_TESTS=1 to run isolated Docker integration tests",
)


@pytest.fixture(scope="module")
def runner() -> DockerJudgeRunner:
    client = docker.from_env()
    client.ping()
    return DockerJudgeRunner(client=client)


def make_request(
    *,
    language: str,
    source_code: str,
    expected_output: str = "",
) -> JudgeRequest:
    return JudgeRequest(
        submission_id=uuid4(),
        language=language,
        source_code=source_code,
        test_cases=[
            JudgeTestCaseRequest(
                id=uuid4(),
                case_index=1,
                name="sample",
                input_text="",
                expected_output_text=expected_output,
                is_sample=True,
            )
        ],
    )


@pytest.mark.parametrize(
    ("language", "source_code"),
    [
        ("python", 'print("ok")'),
        ("cpp", '#include <iostream>\nint main(){std::cout << "ok";}'),
    ],
)
def test_runner_accepts_supported_languages(
    runner: DockerJudgeRunner,
    language: str,
    source_code: str,
) -> None:
    result = runner.run(
        make_request(language=language, source_code=source_code, expected_output="ok\n")
    )

    assert result.verdict == "accepted"
    assert result.passed_case_count == 1


@pytest.mark.parametrize(
    ("language", "source_code", "expected_verdict"),
    [
        ("python", 'print("wrong")', "wrong_answer"),
        ("python", "def broken(:\n    pass", "compile_error"),
        ("python", "raise RuntimeError('boom')", "runtime_error"),
        ("python", "while True:\n    pass", "time_limit_exceeded"),
        ("cpp", '#include <iostream>\nint main(){std::cout << "wrong";}', "wrong_answer"),
        ("cpp", "int main( {", "compile_error"),
        ("cpp", "int main(){int* value=nullptr; return *value;}", "runtime_error"),
        ("cpp", "int main(){while(true){}}", "time_limit_exceeded"),
    ],
)
def test_runner_failure_verdicts(
    runner: DockerJudgeRunner,
    language: str,
    source_code: str,
    expected_verdict: str,
) -> None:
    result = runner.run(
        make_request(language=language, source_code=source_code, expected_output="expected")
    )

    assert result.verdict == expected_verdict


@pytest.mark.parametrize(
    ("language", "source_code"),
    [
        ("python", "import os\nwhile True:\n    os.fork()"),
        ("cpp", "#include <unistd.h>\nint main(){while(true){fork();}}"),
    ],
)
def test_fork_bombs_are_contained(
    runner: DockerJudgeRunner,
    language: str,
    source_code: str,
) -> None:
    result = runner.run(make_request(language=language, source_code=source_code))

    assert result.verdict in {"runtime_error", "time_limit_exceeded"}


def test_network_and_root_filesystem_are_blocked(runner: DockerJudgeRunner) -> None:
    source_code = """
import socket

blocked = 0
try:
    open("/forbidden", "w").write("x")
except OSError:
    blocked += 1
try:
    socket.create_connection(("1.1.1.1", 80), timeout=0.2)
except OSError:
    blocked += 1
print(blocked)
"""
    result = runner.run(
        make_request(language="python", source_code=source_code, expected_output="2\n")
    )

    assert result.verdict == "accepted"


def test_output_limit_is_enforced(runner: DockerJudgeRunner) -> None:
    result = runner.run(
        make_request(language="python", source_code='print("x" * 70000)')
    )

    assert result.verdict == "output_limit_exceeded"


def test_workspace_size_is_bounded(runner: DockerJudgeRunner) -> None:
    result = runner.run(
        make_request(
            language="python",
            source_code=(
                "with open('/workspace/data.bin', 'wb') as output:\n"
                "    output.write(b'x' * (70 * 1024 * 1024))"
            ),
        )
    )

    assert result.verdict == "runtime_error"


def test_memory_limit_is_enforced(
    runner: DockerJudgeRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "judge_case_timeout_seconds", 8)
    monkeypatch.setattr(settings, "judge_total_timeout_seconds", 10)
    result = runner.run(
        make_request(
            language="python",
            source_code=(
                "data = bytearray(1536 * 1024 * 1024)\n"
                "for index in range(0, len(data), 4096):\n"
                "    data[index] = 1\n"
                "print(len(data))"
            ),
        )
    )

    assert result.verdict in {"memory_limit_exceeded", "runtime_error"}
    if result.verdict == "runtime_error":
        assert "memory limit may have been exceeded" in (
            result.case_results[0].error_message or ""
        )


def test_no_runner_containers_remain(runner: DockerJudgeRunner) -> None:
    containers = runner.client.containers.list(
        all=True,
        filters={"label": "algomentor.judge=true"},
    )

    assert containers == []
