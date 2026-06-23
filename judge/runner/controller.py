import json
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import resource
except ModuleNotFoundError:  # Windows test collection; runner execution is Linux-only.
    resource = None


def normalize_output(value: str) -> str:
    lines = value.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    while lines and not lines[-1].rstrip(" \t"):
        lines.pop()
    return "\n".join(line.rstrip(" \t") for line in lines)


def read_oom_kills() -> int | None:
    try:
        values = {}
        for line in Path("/sys/fs/cgroup/memory.events").read_text().splitlines():
            key, value = line.split()
            values[key] = int(value)
        return values.get("oom_kill", 0)
    except (OSError, ValueError):
        return None


def parse_memory_kb(path: Path) -> int | None:
    try:
        match = re.search(
            r"Maximum resident set size \(kbytes\):\s*(\d+)",
            path.read_text(errors="replace"),
        )
        return int(match.group(1)) if match else None
    except OSError:
        return None


def runtime_limits(process_limit: int, output_limit: int):
    def apply() -> None:
        if resource is None:
            raise RuntimeError("Runner resource limits require Linux")
        resource.setrlimit(resource.RLIMIT_NPROC, (process_limit, process_limit))
        resource.setrlimit(resource.RLIMIT_FSIZE, (output_limit, output_limit))
        os.setsid()

    return apply


def safe_read(path: Path, limit: int) -> tuple[str, bool]:
    try:
        data = path.read_bytes()
    except OSError:
        return "", False
    exceeded = len(data) > limit
    return data[:limit].decode("utf-8", errors="replace"), exceeded


def run_case(
    command: list[str],
    case: dict[str, Any],
    *,
    timeout: float,
    process_limit: int,
    output_limit: int,
    workspace: Path,
) -> dict[str, Any]:
    index = case["case_index"]
    stdin_path = workspace / f"case-{index}.in"
    stdout_path = workspace / f"case-{index}.out"
    stderr_path = workspace / f"case-{index}.err"
    time_path = workspace / f"case-{index}.time"
    stdin_path.write_text(case["input_text"])
    oom_before = read_oom_kills()
    started = time.monotonic()
    timed_out = False
    with stdin_path.open("rb") as stdin, stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(
            ["/usr/bin/time", "-v", "-o", str(time_path), "--", *command],
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            cwd=workspace,
            preexec_fn=runtime_limits(process_limit, output_limit),
        )
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except (ProcessLookupError, OSError):
                pass
            return_code = process.wait()
    elapsed_ms = int((time.monotonic() - started) * 1000)
    actual, output_exceeded = safe_read(stdout_path, output_limit)
    stderr_text, stderr_exceeded = safe_read(stderr_path, output_limit)
    output_hit_limit = (
        return_code != 0
        and stdout_path.exists()
        and stdout_path.stat().st_size >= output_limit
    )
    oom_after = read_oom_kills()
    oom_killed = oom_before is not None and oom_after is not None and oom_after > oom_before

    verdict = "accepted"
    error_message = None
    if timed_out:
        verdict = "time_limit_exceeded"
        error_message = "Time limit exceeded"
    elif oom_killed:
        verdict = "memory_limit_exceeded"
        error_message = "Memory limit exceeded"
    elif (
        output_exceeded
        or stderr_exceeded
        or output_hit_limit
        or return_code == -signal.SIGXFSZ
    ):
        verdict = "output_limit_exceeded"
        error_message = "Output limit exceeded"
    elif return_code != 0:
        verdict = "runtime_error"
        error_message = (
            "Process was killed; memory limit may have been exceeded"
            if return_code in (137, -signal.SIGKILL)
            else (stderr_text.strip()[:300] or "Runtime error")
        )
    elif normalize_output(actual) != normalize_output(case["expected_output_text"]):
        verdict = "wrong_answer"

    return {
        "test_case_id": case["id"],
        "case_index": index,
        "name": case.get("name"),
        "is_sample": case["is_sample"],
        "verdict": verdict,
        "execution_time_ms": elapsed_ms,
        "memory_kb": parse_memory_kb(time_path),
        "actual_output": actual if case["is_sample"] else None,
        "error_message": error_message,
    }


def compile_source(payload: dict[str, Any], workspace: Path, timeout: int) -> tuple[list[str] | None, str | None]:
    language = payload["language"]
    if language == "cpp":
        source = workspace / "source.cpp"
        source.write_text(payload["source_code"])
        try:
            result = subprocess.run(
                ["g++", "-std=c++17", "-O2", "-pipe", "-DONLINE_JUDGE", str(source), "-o", str(workspace / "main")],
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None, "Compilation timed out"
        if result.returncode != 0:
            return None, (result.stderr or result.stdout)[:65536]
        return [str(workspace / "main")], None

    source = workspace / "source.py"
    source.write_text(payload["source_code"])
    try:
        result = subprocess.run(
            ["python3", "-I", "-B", "-m", "py_compile", str(source)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, "Syntax check timed out"
    if result.returncode != 0:
        return None, (result.stderr or result.stdout)[:65536]
    return ["python3", "-I", "-B", str(source)], None


def write_result(result_path: str, result: dict[str, Any]) -> None:
    content = json.dumps(result)
    if result_path == "-":
        sys.stdout.write(content)
        sys.stdout.flush()
        return
    Path(result_path).write_text(content)


def main(request_path: str, result_path: str) -> None:
    payload = json.loads(Path(request_path).read_text())
    limits = payload["limits"]
    workspace = Path(request_path).parent
    command, compile_error = compile_source(payload, workspace, limits["compile_timeout_seconds"])
    if compile_error is not None:
        result = {
            "verdict": "compile_error",
            "passed_case_count": 0,
            "total_case_count": len(payload["test_cases"]),
            "compile_output": compile_error,
            "case_results": [
                {
                    "test_case_id": case["id"],
                    "case_index": case["case_index"],
                    "name": case.get("name"),
                    "is_sample": case["is_sample"],
                    "verdict": "not_run",
                }
                for case in payload["test_cases"]
            ],
        }
        write_result(result_path, result)
        return

    started = time.monotonic()
    case_results = []
    for position, case in enumerate(payload["test_cases"]):
        remaining = limits["total_timeout_seconds"] - (time.monotonic() - started)
        if remaining <= 0:
            case_results.extend(
                {
                    "test_case_id": pending["id"],
                    "case_index": pending["case_index"],
                    "name": pending.get("name"),
                    "is_sample": pending["is_sample"],
                    "verdict": "not_run",
                }
                for pending in payload["test_cases"][position:]
            )
            break
        case_results.append(
            run_case(
                command,
                case,
                timeout=min(limits["case_timeout_seconds"], remaining),
                process_limit=limits["runtime_process_limit"],
                output_limit=limits["output_limit_bytes"],
                workspace=workspace,
            )
        )

    passed = sum(item["verdict"] == "accepted" for item in case_results)
    first_failure = next((item["verdict"] for item in case_results if item["verdict"] != "accepted"), None)
    if first_failure == "not_run":
        verdict = "time_limit_exceeded"
    else:
        verdict = first_failure or "accepted"
    result = {
        "verdict": verdict,
        "passed_case_count": passed,
        "total_case_count": len(payload["test_cases"]),
        "execution_time_ms": int((time.monotonic() - started) * 1000),
        "memory_kb": max(
            (item["memory_kb"] for item in case_results if item.get("memory_kb") is not None),
            default=None,
        ),
        "case_results": case_results,
    }
    write_result(result_path, result)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
