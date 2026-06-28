from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings
from app.schemas.openmaic import OpenMAICGeneratePayload, OpenMAICJobStatus
from app.services.openmaic import HttpOpenMAICClient, OpenMAICClientError
from app.services.openmaic.client import sanitize_openmaic_base_url


SAMPLE_REQUIREMENT = """请生成一节中文互动算法课堂。
主题：双指针入门
受众：算法入门学生
目标：理解左右指针、快慢指针和常见边界错误
要求：使用中文讲解，包含互动提问、小测验和可视化演示建议。"""

TERMINAL_STATUSES = {"completed", "failed"}


def _masked(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "***"
    return f"{value[:2]}***{value[-2:]}"


def _print_config() -> None:
    try:
        base_url = sanitize_openmaic_base_url(settings.openmaic_base_url)
    except OpenMAICClientError as exc:
        base_url = f"<invalid: {exc.code}>"

    print("OpenMAIC integration check")
    print(f"- enabled: {settings.enable_openmaic_integration}")
    print(f"- base_url: {base_url}")
    print(f"- generate_path: {settings.openmaic_generate_path}")
    print(f"- poll_path_template: {settings.openmaic_poll_path_template}")
    print(f"- auth_mode: {settings.openmaic_auth_mode}")
    if settings.openmaic_auth_mode == "header":
        print(f"- auth_header_name: {settings.openmaic_auth_header_name}")
        print(f"- auth_header_value: {_masked(settings.openmaic_auth_header_value)}")
    elif settings.openmaic_auth_mode == "query":
        print(f"- auth_query_name: {settings.openmaic_auth_query_name}")
        print(f"- auth_query_value: {_masked(settings.openmaic_auth_query_value)}")
    elif settings.openmaic_auth_mode == "body":
        print(f"- auth_body_field: {settings.openmaic_auth_body_field}")
        print(f"- auth_body_value: {_masked(settings.openmaic_auth_body_value)}")


def _print_openmaic_start_hint() -> None:
    print("Hint: start OpenMAIC in another terminal:")
    print(r"  cd D:\OpenMAIC")
    print("  pnpm dev --port 3010")


def _dump_result(label: str, result: OpenMAICJobStatus) -> None:
    print(f"{label}: {result.model_dump()}")


async def _poll_until_done(
    client: HttpOpenMAICClient,
    job_id: str,
    *,
    timeout_minutes: float,
    interval_seconds: float,
) -> OpenMAICJobStatus:
    deadline = time.monotonic() + timeout_minutes * 60
    last_result: OpenMAICJobStatus | None = None
    attempt = 0
    while time.monotonic() <= deadline:
        attempt += 1
        result = await client.get_job(job_id)
        last_result = result
        _dump_result(f"Poll normalized result #{attempt}", result)
        if result.status in TERMINAL_STATUSES:
            return result
        await asyncio.sleep(interval_seconds)
    if last_result is None:
        raise OpenMAICClientError(
            "OPENMAIC_TIMEOUT",
            "OpenMAIC polling timed out before the first status response",
            status_code=504,
        )
    return last_result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the external OpenMAIC integration.")
    parser.add_argument(
        "--no-wait",
        action="store_true",
        help="Generate a classroom and perform at most one poll instead of waiting for completion.",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=float,
        default=float(settings.openmaic_max_poll_minutes),
        help="Maximum minutes to wait for completion. Defaults to OPENMAIC_MAX_POLL_MINUTES.",
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=5.0,
        help="Polling interval in seconds. Defaults to 5.",
    )
    return parser.parse_args()


async def main() -> int:
    args = _parse_args()
    _print_config()
    if not settings.enable_openmaic_integration:
        print("Result: FEATURE_DISABLED")
        return 1

    try:
        client = HttpOpenMAICClient()
        generated = await client.generate_classroom(OpenMAICGeneratePayload(requirement=SAMPLE_REQUIREMENT))
        _dump_result("Generate normalized result", generated)

        if not generated.job_id:
            print("Poll skipped: no job_id returned")
            return 0 if generated.status == "completed" and generated.classroom_url else 1

        if args.no_wait:
            polled = await client.get_job(generated.job_id)
        else:
            polled = await _poll_until_done(
                client,
                generated.job_id,
                timeout_minutes=max(args.timeout_minutes, 0.1),
                interval_seconds=max(args.interval_seconds, 0.5),
            )

        if args.no_wait:
            _dump_result("Poll normalized result", polled)
        if polled.status == "completed" and polled.classroom_url:
            print(f"Result: completed, classroom_url={polled.classroom_url}")
            return 0
        if polled.status == "failed":
            print("Result: failed")
            return 1
        print(f"Result: still {polled.status}; run again later or increase --timeout-minutes")
        return 1
    except OpenMAICClientError as exc:
        print(f"Result: {exc.code} ({exc.status_code})")
        print(f"Message: {exc.message}")
        if exc.code == "OPENMAIC_UNAVAILABLE":
            _print_openmaic_start_hint()
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
