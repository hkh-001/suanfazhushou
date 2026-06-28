from __future__ import annotations

import asyncio

from app.core.config import settings
from app.schemas.openmaic import OpenMAICGeneratePayload
from app.services.openmaic import HttpOpenMAICClient, OpenMAICClientError
from app.services.openmaic.client import sanitize_openmaic_base_url


SAMPLE_REQUIREMENT = """请生成一节中文互动算法课堂。
主题：双指针入门
受众：算法入门学生
目标：理解左右指针、快慢指针和常见边界错误
要求：使用中文讲解，包含互动提问、小测验和可视化演示建议。"""


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


async def main() -> int:
    _print_config()
    if not settings.enable_openmaic_integration:
        print("Result: FEATURE_DISABLED")
        return 1

    try:
        client = HttpOpenMAICClient()
        generated = await client.generate_classroom(OpenMAICGeneratePayload(requirement=SAMPLE_REQUIREMENT))
        print(f"Generate normalized result: {generated.model_dump()}")

        if generated.job_id:
            polled = await client.get_job(generated.job_id)
            print(f"Poll normalized result: {polled.model_dump()}")
        else:
            print("Poll skipped: no job_id returned")
        return 0
    except OpenMAICClientError as exc:
        print(f"Result: {exc.code} ({exc.status_code})")
        print(f"Message: {exc.message}")
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
