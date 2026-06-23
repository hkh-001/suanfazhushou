import asyncio
import json
import socket
import time
from datetime import datetime, timezone
from typing import Any

import docker
from docker.errors import APIError, NotFound

from app.config import settings
from app.schemas import CaseResult, JudgeRequest, JudgeResponse


def _request_bytes(payload: JudgeRequest) -> bytes:
    return json.dumps(
        {
            **payload.model_dump(mode="json"),
            "limits": {
                "compile_timeout_seconds": settings.judge_compile_timeout_seconds,
                "case_timeout_seconds": settings.judge_case_timeout_seconds,
                "total_timeout_seconds": settings.judge_total_timeout_seconds,
                "runtime_process_limit": settings.judge_runtime_process_limit,
                "output_limit_bytes": settings.judge_output_limit_bytes,
            },
        },
        ensure_ascii=True,
    ).encode()


def _write_request(container: Any, content: bytes) -> None:
    exec_id = container.client.api.exec_create(
        container.id,
        ["sh", "-c", "cat > /workspace/request.json"],
        stdin=True,
        stdout=True,
        stderr=True,
        user="10001:10001",
    )["Id"]
    stream = container.client.api.exec_start(exec_id, socket=True)
    try:
        raw_socket = getattr(stream, "_sock", stream)
        raw_socket.sendall(content)
        try:
            raw_socket.shutdown(socket.SHUT_WR)
        except (OSError, RuntimeError):
            pass
    finally:
        stream.close()
    result = container.client.api.exec_inspect(exec_id)
    deadline = time.monotonic() + 5
    while result.get("Running") and time.monotonic() < deadline:
        time.sleep(0.05)
        result = container.client.api.exec_inspect(exec_id)
    if result.get("ExitCode") != 0:
        raise RuntimeError("Failed to transfer judge request")


def _container_oom_kills(container: Any) -> int | None:
    result = container.exec_run(
        ["sh", "-c", "awk '$1 == \"oom_kill\" {print $2}' /sys/fs/cgroup/memory.events"],
        user="10001:10001",
    )
    if result.exit_code != 0:
        return None
    try:
        return int(result.output.decode().strip())
    except (UnicodeDecodeError, ValueError):
        return None


def _fatal_response(
    payload: JudgeRequest,
    *,
    verdict: str,
    message: str,
) -> JudgeResponse:
    return JudgeResponse(
        verdict=verdict,
        passed_case_count=0,
        total_case_count=len(payload.test_cases),
        error_message=message,
        case_results=[
            CaseResult(
                test_case_id=case.id,
                case_index=case.case_index,
                name=case.name,
                is_sample=case.is_sample,
                verdict=verdict if index == 0 else "not_run",
                error_message=message if index == 0 else None,
            )
            for index, case in enumerate(payload.test_cases)
        ],
    )


class DockerJudgeRunner:
    def __init__(self, client: Any | None = None) -> None:
        self.client = client or docker.from_env(timeout=settings.judge_request_hard_timeout_seconds)

    def _container_config(self, payload: JudgeRequest) -> dict[str, Any]:
        started_at = datetime.now(timezone.utc).isoformat()
        return {
            "image": settings.judge_runner_image,
            "command": ["sleep", str(settings.judge_request_hard_timeout_seconds + 5)],
            "detach": True,
            "network_disabled": True,
            "read_only": True,
            "mem_limit": f"{settings.judge_memory_limit_mb}m",
            "nano_cpus": int(settings.judge_cpu_limit * 1_000_000_000),
            "pids_limit": settings.judge_container_pids_limit,
            "cap_drop": ["ALL"],
            "security_opt": ["no-new-privileges:true"],
            "tmpfs": {
                "/workspace": (
                    f"rw,exec,nosuid,nodev,size={settings.judge_workspace_limit_mb}m,"
                    "uid=10001,gid=10001,mode=700"
                )
            },
            "user": "10001:10001",
            "labels": {
                "algomentor.judge": "true",
                "algomentor.submission_id": str(payload.submission_id),
                "algomentor.started_at": started_at,
            },
        }

    def run(self, payload: JudgeRequest) -> JudgeResponse:
        container = None
        try:
            container = self.client.containers.create(**self._container_config(payload))
            container.start()
            _write_request(container, _request_bytes(payload))
            oom_before = _container_oom_kills(container)
            exec_result = container.exec_run(
                [
                    "python",
                    "/opt/runner/controller.py",
                    "/workspace/request.json",
                    "-",
                ],
                user="10001:10001",
            )
            oom_after = _container_oom_kills(container)
            container.reload()
            if exec_result.exit_code == 0 and exec_result.output:
                return JudgeResponse.model_validate_json(exec_result.output)
            if (
                container.attrs.get("State", {}).get("OOMKilled")
                or (
                    oom_before is not None
                    and oom_after is not None
                    and oom_after > oom_before
                )
            ):
                return _fatal_response(
                    payload,
                    verdict="memory_limit_exceeded",
                    message="Memory limit exceeded",
                )
            if exec_result.exit_code in (137, -9):
                return _fatal_response(
                    payload,
                    verdict="runtime_error",
                    message="Process was killed; memory limit may have been exceeded",
                )
            return JudgeResponse(
                verdict="internal_error",
                passed_case_count=0,
                total_case_count=len(payload.test_cases),
                error_message=f"Runner exited without a result ({exec_result.exit_code})",
            )
        except Exception as exc:
            if isinstance(exc, (APIError, NotFound)):
                message = "Runner container failed"
            else:
                message = "Judge execution failed"
            return JudgeResponse(
                verdict="internal_error",
                passed_case_count=0,
                total_case_count=len(payload.test_cases),
                error_message=message,
            )
        finally:
            if container is not None:
                try:
                    container.kill()
                except Exception:
                    pass
                try:
                    container.remove(force=True)
                except Exception:
                    pass

    async def run_async(self, payload: JudgeRequest) -> JudgeResponse:
        task = asyncio.create_task(asyncio.to_thread(self.run, payload))
        try:
            return await asyncio.wait_for(
                asyncio.shield(task),
                timeout=settings.judge_request_hard_timeout_seconds,
            )
        except asyncio.TimeoutError:
            task.add_done_callback(
                lambda completed: (
                    completed.exception() if not completed.cancelled() else None
                )
            )
            return JudgeResponse(
                verdict="internal_error",
                passed_case_count=0,
                total_case_count=len(payload.test_cases),
                error_message="Judge execution deadline exceeded",
            )
        except asyncio.CancelledError:
            try:
                await asyncio.shield(task)
            finally:
                raise

    def cleanup_stale(self) -> None:
        for container in self.client.containers.list(
            all=True,
            filters={"label": "algomentor.judge=true"},
        ):
            try:
                started_at = container.labels.get("algomentor.started_at", "")
                started = datetime.fromisoformat(started_at)
                age = (datetime.now(timezone.utc) - started).total_seconds()
            except (TypeError, ValueError):
                age = settings.judge_stale_container_seconds + 1
            if age <= settings.judge_stale_container_seconds:
                continue
            try:
                container.kill()
            except Exception:
                pass
            try:
                container.remove(force=True)
            except Exception:
                pass
