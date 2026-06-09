from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ai_call_log import AICallLog


def create_ai_call_log(
    db: Session,
    *,
    user_id: UUID,
    provider: str,
    model: str,
    prompt_type: str,
    input_tokens: int | None,
    output_tokens: int | None,
    latency_ms: int,
    success: bool,
    error_code: str | None = None,
    error_message: str | None = None,
) -> AICallLog:
    log = AICallLog(
        user_id=user_id,
        provider=provider,
        model=model,
        prompt_type=prompt_type,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        success=success,
        error_code=error_code,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
