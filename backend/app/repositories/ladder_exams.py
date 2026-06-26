from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ladder import LearningPath
from app.models.ladder_exam import LadderExamAttempt


def get_latest_generated_attempt(
    db: Session,
    *,
    user_id: UUID,
    node_id: UUID,
) -> LadderExamAttempt | None:
    stmt = (
        select(LadderExamAttempt)
        .where(
            LadderExamAttempt.user_id == user_id,
            LadderExamAttempt.node_id == node_id,
            LadderExamAttempt.status == "generated",
        )
        .order_by(LadderExamAttempt.created_at.desc(), LadderExamAttempt.id.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def get_attempt_for_user(db: Session, *, attempt_id: UUID, user_id: UUID) -> LadderExamAttempt | None:
    stmt = (
        select(LadderExamAttempt)
        .options(
            selectinload(LadderExamAttempt.node),
            selectinload(LadderExamAttempt.path).selectinload(LearningPath.nodes),
        )
        .where(LadderExamAttempt.id == attempt_id, LadderExamAttempt.user_id == user_id)
    )
    return db.scalar(stmt)


def get_latest_submitted_attempt_for_node(
    db: Session,
    *,
    user_id: UUID,
    node_id: UUID,
) -> LadderExamAttempt | None:
    stmt = (
        select(LadderExamAttempt)
        .where(
            LadderExamAttempt.user_id == user_id,
            LadderExamAttempt.node_id == node_id,
            LadderExamAttempt.status == "submitted",
        )
        .order_by(LadderExamAttempt.submitted_at.desc(), LadderExamAttempt.created_at.desc(), LadderExamAttempt.id.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def create_exam_attempt(
    db: Session,
    *,
    user_id: UUID,
    path_id: UUID,
    node_id: UUID,
    exam_payload: dict,
    model: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> LadderExamAttempt:
    attempt = LadderExamAttempt(
        user_id=user_id,
        path_id=path_id,
        node_id=node_id,
        status="generated",
        exam_payload=exam_payload,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def submit_exam_attempt(
    db: Session,
    *,
    attempt: LadderExamAttempt,
    submitted_answers: dict,
    result_payload: dict,
    score: int,
    passed: bool,
) -> LadderExamAttempt:
    attempt.status = "submitted"
    attempt.submitted_answers = submitted_answers
    attempt.result_payload = result_payload
    attempt.score = score
    attempt.passed = passed
    attempt.submitted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)
    return attempt
