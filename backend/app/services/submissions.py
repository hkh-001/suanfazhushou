from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.problem import Problem
from app.models.submission import Submission, SubmissionCaseResult
from app.models.test_case import TestCase
from app.models.user import User
from app.providers.ai.base import AIProvider
from app.repositories.problems import get_accessible_problem_with_test_cases
from app.repositories.submissions import create_submission as insert_submission
from app.repositories.submissions import get_user_submission
from app.schemas.judge import JudgeRequest, JudgeTestCaseRequest
from app.schemas.submission import (
    SubmissionCaseResultDetail,
    SubmissionCreate,
    SubmissionDetail,
    SubmissionDiagnosisResponse,
    SubmissionProblemRef,
)
from app.services.ai.service import AIService
from app.services.judge.client import JudgeClient
from app.services.submission_limiter import SubmissionLimiter

PROBLEM_NOT_FOUND = {"code": "PROBLEM_NOT_FOUND", "message": "Problem not found"}
SUBMISSION_NOT_FOUND = {"code": "SUBMISSION_NOT_FOUND", "message": "Submission not found"}
TEST_CASES_REQUIRED = {
    "code": "PROBLEM_TEST_CASES_REQUIRED",
    "message": "Problem has no test cases",
}
INVALID_JUDGE_RESPONSE = {
    "code": "JUDGE_INVALID_RESPONSE",
    "message": "Judge returned an invalid response",
}
DIAGNOSIS_NOT_AVAILABLE = {
    "code": "SUBMISSION_DIAGNOSIS_NOT_AVAILABLE",
    "message": "AI diagnosis is not available for this submission verdict",
}
DIAGNOSABLE_VERDICTS = {
    "compile_error",
    "wrong_answer",
    "runtime_error",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "output_limit_exceeded",
}


def _invalid_judge_response() -> HTTPException:
    return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=INVALID_JUDGE_RESPONSE)


def _to_detail(submission: Submission) -> SubmissionDetail:
    return SubmissionDetail(
        id=submission.id,
        problem=SubmissionProblemRef(
            id=submission.problem_id,
            display_id=submission.problem_display_id,
            title=submission.problem_title,
        ),
        language=submission.language,
        source_code=submission.source_code,
        verdict=submission.verdict,
        passed_case_count=submission.passed_case_count,
        total_case_count=submission.total_case_count,
        execution_time_ms=submission.execution_time_ms,
        memory_kb=submission.memory_kb,
        compile_output=submission.compile_output,
        error_message=submission.error_message,
        case_results=[
            SubmissionCaseResultDetail(
                case_index=result.case_index,
                name=result.name,
                is_sample=result.is_sample,
                verdict=result.verdict,
                execution_time_ms=result.execution_time_ms,
                memory_kb=result.memory_kb,
                input_text=result.input_text if result.is_sample else None,
                expected_output_text=result.expected_output_text if result.is_sample else None,
                actual_output=result.actual_output if result.is_sample else None,
                error_message=result.error_message,
            )
            for result in submission.case_results
        ],
        created_at=submission.created_at,
        finished_at=submission.finished_at,
    )


async def create_submission(
    db: Session,
    *,
    user: User,
    payload: SubmissionCreate,
    judge_client: JudgeClient,
    limiter: SubmissionLimiter,
) -> SubmissionDetail:
    if not settings.enable_code_execution:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "CODE_EXECUTION_DISABLED", "message": "Code execution is disabled"},
        )
    if not settings.judge_base_url.strip() or not settings.judge_internal_token.strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "JUDGE_CONFIG_MISSING", "message": "Judge configuration is missing"},
        )

    problem = get_accessible_problem_with_test_cases(db, problem_id=payload.problem_id, user_id=user.id)
    if problem is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROBLEM_NOT_FOUND)
    test_cases = sorted(problem.test_cases, key=lambda item: item.case_index)
    if not test_cases:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=TEST_CASES_REQUIRED)

    submission_id = uuid4()
    user_id = user.id
    problem_id = problem.id
    problem_title = problem.title
    problem_display_id = problem.display_id
    test_case_snapshots = [
        {
            "id": case.id,
            "case_index": case.case_index,
            "name": case.name,
            "input_text": case.input_text,
            "expected_output_text": case.expected_output_text,
            "is_sample": case.is_sample,
        }
        for case in test_cases
    ]
    db.rollback()
    db.close()

    await limiter.acquire()
    try:
        judge_result = await judge_client.judge(
            JudgeRequest(
                submission_id=submission_id,
                language=payload.language,
                source_code=payload.source_code,
                test_cases=[JudgeTestCaseRequest(**item) for item in test_case_snapshots],
            )
        )
    finally:
        await limiter.release()

    snapshots_by_id = {item["id"]: item for item in test_case_snapshots}
    accepted_case_count = sum(
        result.verdict == "accepted" for result in judge_result.case_results
    )
    if (
        judge_result.total_case_count != len(test_case_snapshots)
        or judge_result.passed_case_count > judge_result.total_case_count
        or (
            judge_result.verdict != "internal_error"
            and (
                len(judge_result.case_results) != len(test_case_snapshots)
                or judge_result.passed_case_count != accepted_case_count
            )
        )
    ):
        raise _invalid_judge_response()

    returned_ids = [result.test_case_id for result in judge_result.case_results]
    if len(returned_ids) != len(set(returned_ids)):
        raise _invalid_judge_response()

    existing_problem_id = problem_id if db.get(Problem, problem_id) is not None else None
    existing_test_case_ids = set(
        db.scalars(select(TestCase.id).where(TestCase.id.in_(snapshots_by_id))).all()
    )
    case_results: list[SubmissionCaseResult] = []
    for result in judge_result.case_results:
        snapshot = snapshots_by_id.get(result.test_case_id)
        if (
            snapshot is None
            or result.case_index != snapshot["case_index"]
            or result.is_sample != snapshot["is_sample"]
        ):
            raise _invalid_judge_response()
        case_results.append(
            SubmissionCaseResult(
                test_case_id=(
                    result.test_case_id if result.test_case_id in existing_test_case_ids else None
                ),
                case_index=result.case_index,
                name=result.name,
                is_sample=result.is_sample,
                verdict=result.verdict,
                execution_time_ms=result.execution_time_ms,
                memory_kb=result.memory_kb,
                input_text=snapshot["input_text"] if result.is_sample else None,
                expected_output_text=snapshot["expected_output_text"] if result.is_sample else None,
                actual_output=result.actual_output if result.is_sample else None,
                error_message=result.error_message,
            )
        )

    submission = Submission(
        id=submission_id,
        user_id=user_id,
        problem_id=existing_problem_id,
        problem_title=problem_title,
        problem_display_id=problem_display_id,
        language=payload.language,
        source_code=payload.source_code,
        verdict=judge_result.verdict,
        passed_case_count=judge_result.passed_case_count,
        total_case_count=judge_result.total_case_count,
        execution_time_ms=judge_result.execution_time_ms,
        memory_kb=judge_result.memory_kb,
        compile_output=judge_result.compile_output,
        error_message=judge_result.error_message,
        finished_at=datetime.now(timezone.utc),
    )
    saved = insert_submission(db, submission=submission, case_results=case_results)
    return _to_detail(saved)


def get_submission(db: Session, *, user: User, submission_id: UUID) -> SubmissionDetail:
    submission = get_user_submission(db, submission_id=submission_id, user_id=user.id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SUBMISSION_NOT_FOUND)
    return _to_detail(submission)


def diagnose_submission(
    db: Session,
    *,
    user: User,
    submission_id: UUID,
    provider: AIProvider,
) -> SubmissionDiagnosisResponse:
    submission = get_user_submission(db, submission_id=submission_id, user_id=user.id)
    if submission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=SUBMISSION_NOT_FOUND)
    if submission.verdict not in DIAGNOSABLE_VERDICTS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=DIAGNOSIS_NOT_AVAILABLE,
        )
    return AIService(db, provider).diagnose_submission(user=user, submission=submission)
