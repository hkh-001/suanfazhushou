from typing import Any, Protocol
from urllib.parse import quote, urljoin, urlparse, urlunparse

import httpx

from app.core.config import settings
from app.schemas.openmaic import OpenMAICGeneratePayload, OpenMAICJobStatus


class OpenMAICClientError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class OpenMAICClient(Protocol):
    async def generate_classroom(self, payload: OpenMAICGeneratePayload) -> OpenMAICJobStatus: ...

    async def get_job(self, job_id: str) -> OpenMAICJobStatus: ...


def sanitize_openmaic_base_url(base_url: str) -> str:
    value = base_url.strip()
    if not value:
        raise OpenMAICClientError(
            "OPENMAIC_CONFIG_MISSING",
            "OpenMAIC base URL is not configured",
            status_code=503,
        )
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise OpenMAICClientError(
            "OPENMAIC_CONFIG_MISSING",
            "OpenMAIC base URL is invalid",
            status_code=503,
        )
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))


class HttpOpenMAICClient:
    def __init__(self) -> None:
        self.base_url = sanitize_openmaic_base_url(settings.openmaic_base_url)
        self.generate_path = _normalize_path(settings.openmaic_generate_path)
        self.poll_path_template = _normalize_path(settings.openmaic_poll_path_template)
        self.timeout = settings.openmaic_request_timeout_seconds
        self.auth_mode = settings.openmaic_auth_mode.strip().lower() or "none"

    async def generate_classroom(self, payload: OpenMAICGeneratePayload) -> OpenMAICJobStatus:
        body = _payload_body(payload)
        url = self._url(self.generate_path)
        url, headers, body = self._apply_auth(url, {}, body)
        response = await self._request("POST", url, headers=headers, json=body, not_found_code="OPENMAIC_UNAVAILABLE")
        return _parse_job_status(response)

    async def get_job(self, job_id: str) -> OpenMAICJobStatus:
        safe_job_id = quote(job_id, safe="")
        path = self.poll_path_template.replace("{job_id}", safe_job_id)
        url = self._url(path)
        url, headers, body = self._apply_auth(url, {}, None)
        response = await self._request("GET", url, headers=headers, json=body, not_found_code="OPENMAIC_JOB_NOT_FOUND")
        return _parse_job_status(response, fallback_job_id=job_id)

    def _url(self, path: str) -> str:
        return urljoin(f"{self.base_url}/", path.lstrip("/"))

    def _apply_auth(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> tuple[str, dict[str, str], dict[str, Any] | None]:
        if self.auth_mode == "none":
            return url, headers, body
        if self.auth_mode == "header":
            name = settings.openmaic_auth_header_name.strip()
            value = settings.openmaic_auth_header_value
            if name and value:
                headers[name] = value
            return url, headers, body
        if self.auth_mode == "query":
            name = settings.openmaic_auth_query_name.strip()
            value = settings.openmaic_auth_query_value
            if name and value:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}{quote(name, safe='')}={quote(value, safe='')}"
            return url, headers, body
        if self.auth_mode == "body":
            name = settings.openmaic_auth_body_field.strip()
            value = settings.openmaic_auth_body_value
            if name and value:
                body = dict(body or {})
                body[name] = value
            return url, headers, body
        raise OpenMAICClientError(
            "OPENMAIC_CONFIG_MISSING",
            "OpenMAIC auth mode is invalid",
            status_code=503,
        )

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        json: dict[str, Any] | None,
        not_found_code: str,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=headers, json=json)
        except httpx.TimeoutException as exc:
            raise OpenMAICClientError(
                "OPENMAIC_TIMEOUT",
                "OpenMAIC request timed out",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise OpenMAICClientError(
                "OPENMAIC_UNAVAILABLE",
                "OpenMAIC service is unavailable",
                status_code=503,
            ) from exc

        if response.status_code == 404:
            if not_found_code == "OPENMAIC_UNAVAILABLE":
                raise OpenMAICClientError(
                    "OPENMAIC_UNAVAILABLE",
                    "OpenMAIC service is unavailable",
                    status_code=503,
                )
            raise OpenMAICClientError(
                "OPENMAIC_JOB_NOT_FOUND",
                "OpenMAIC job was not found",
                status_code=404,
            )
        if not response.is_success:
            raise OpenMAICClientError(
                "OPENMAIC_UNAVAILABLE",
                "OpenMAIC service is unavailable",
                status_code=503,
            )
        return response


def _normalize_path(path: str) -> str:
    value = path.strip() or "/"
    return value if value.startswith("/") else f"/{value}"


def _payload_body(payload: OpenMAICGeneratePayload) -> dict[str, Any]:
    return {
        "requirement": payload.requirement,
        "language": payload.language,
        "enableTTS": payload.enable_tts,
        "enableImageGeneration": payload.enable_image_generation,
        "enableVideoGeneration": payload.enable_video_generation,
        "webSearch": payload.web_search,
    }


def _parse_job_status(response: httpx.Response, *, fallback_job_id: str | None = None) -> OpenMAICJobStatus:
    try:
        data = response.json()
    except ValueError as exc:
        raise OpenMAICClientError(
            "OPENMAIC_INVALID_RESPONSE",
            "OpenMAIC returned an invalid response",
            status_code=502,
        ) from exc
    if not isinstance(data, dict):
        raise OpenMAICClientError(
            "OPENMAIC_INVALID_RESPONSE",
            "OpenMAIC returned an invalid response",
            status_code=502,
        )

    status = _normalize_status(_first_string(data, "status", "state") or ("submitted" if response.status_code == 202 else None))
    job_id = _first_string(data, "jobId", "job_id", "id") or fallback_job_id
    poll_url = _first_string(data, "pollUrl", "poll_url", "statusUrl", "status_url")
    classroom_url = _first_string(data, "classroomUrl", "classroom_url", "url", "resultUrl", "result_url")
    message = _first_string(data, "message", "error", "detail")

    nested = data.get("data") or data.get("result")
    if isinstance(nested, dict):
        status = _normalize_status(_first_string(nested, "status", "state")) or status
        job_id = _first_string(nested, "jobId", "job_id", "id") or job_id
        poll_url = _first_string(nested, "pollUrl", "poll_url", "statusUrl", "status_url") or poll_url
        classroom_url = _first_string(nested, "classroomUrl", "classroom_url", "url", "resultUrl", "result_url") or classroom_url
        message = _first_string(nested, "message", "error", "detail") or message

    if not job_id and not classroom_url:
        raise OpenMAICClientError(
            "OPENMAIC_INVALID_RESPONSE",
            "OpenMAIC returned an invalid response",
            status_code=502,
        )
    return OpenMAICJobStatus(
        status=status or "unknown",
        job_id=job_id,
        poll_url=poll_url,
        classroom_url=classroom_url,
        message=message,
    )


def _first_string(data: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = data.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def _normalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"submitted", "queued", "accepted"}:
        return "submitted"
    if normalized in {"pending"}:
        return "pending"
    if normalized in {"processing", "running", "generating", "in_progress"}:
        return "processing"
    if normalized in {"completed", "complete", "done", "success", "succeeded", "ready"}:
        return "completed"
    if normalized in {"failed", "error", "errored"}:
        return "failed"
    return "unknown"
