from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ladder_exam import LadderExamAttempt
from app.models.user import User
from app.repositories.ladder import get_active_path, get_path_node_for_user, get_progress_for_path, mark_exam_passed
from app.repositories.ladder_exams import (
    create_exam_attempt,
    get_attempt_for_user,
    get_latest_generated_attempt,
    submit_exam_attempt,
)
from app.schemas.ladder_exam import (
    LadderExamAnswer,
    LadderExamAttemptDetail,
    LadderExamGenerationResult,
    LadderExamPayload,
    LadderExamPublicQuestion,
    LadderExamQuestionResult,
    LadderExamSubmitRequest,
    LadderExamSubmitResult,
)
from app.services.ai.service import AIService
from app.services.ladder import (
    LADDER_NODE_NOT_FOUND,
    NODE_LOCKED,
    _node_status,
    _to_summary,
)


LADDER_EXAM_NOT_FOUND = {"code": "LADDER_EXAM_NOT_FOUND", "message": "Learning ladder exam not found"}
LADDER_EXAM_ALREADY_PASSED = {
    "code": "LADDER_EXAM_ALREADY_PASSED",
    "message": "Learning ladder exam has already been passed",
}
LADDER_EXAM_REQUIRE_MATERIAL = {
    "code": "LADDER_EXAM_REQUIRE_MATERIAL",
    "message": "Complete the node material before generating an exam",
}
LADDER_EXAM_REQUIRE_PRACTICE = {
    "code": "LADDER_EXAM_REQUIRE_PRACTICE",
    "message": "Complete the node practice before generating an exam",
}
LADDER_EXAM_VALIDATION_ERROR = {
    "code": "LADDER_EXAM_VALIDATION_ERROR",
    "message": "Learning ladder exam submission is invalid",
}
LADDER_PATH_CREATE_FAILED = {
    "code": "LADDER_PATH_CREATE_FAILED",
    "message": "Learning ladder path could not be loaded",
}


def _public_attempt(attempt: LadderExamAttempt) -> LadderExamAttemptDetail:
    payload = LadderExamPayload.model_validate(attempt.exam_payload)
    submitted = attempt.status == "submitted"
    questions = [
        LadderExamPublicQuestion(
            id=question.id,
            type=question.type,
            prompt=question.prompt,
            options=question.options,
            correct_option_id=question.correct_option_id if submitted else None,
            explanation=question.explanation if submitted else None,
        )
        for question in payload.questions
    ]
    submitted_answers = None
    if isinstance(attempt.submitted_answers, dict):
        submitted_answers = [
            LadderExamAnswer(question_id=item["question_id"], option_id=item["option_id"])
            for item in attempt.submitted_answers.get("answers", [])
            if isinstance(item, dict)
        ]
    results = None
    if isinstance(attempt.result_payload, dict):
        results = [LadderExamQuestionResult.model_validate(item) for item in attempt.result_payload.get("results", [])]
    return LadderExamAttemptDetail(
        id=attempt.id,
        node_id=attempt.node_id,
        status=attempt.status,
        questions=questions,
        score=attempt.score,
        passed=attempt.passed,
        submitted_answers=submitted_answers,
        results=results,
        created_at=attempt.created_at,
        submitted_at=attempt.submitted_at,
    )


def _get_node_and_progress(db: Session, *, user: User, node_id: UUID):
    node = get_path_node_for_user(db, node_id=node_id, user_id=user.id)
    if node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)
    nodes = sorted(node.path.nodes, key=lambda item: item.node_index)
    progress_by_node = get_progress_for_path(db, path=node.path, user_id=user.id)
    progress = progress_by_node.get(node.id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)
    return node, nodes, progress_by_node, progress


def generate_ladder_exam(
    db: Session,
    *,
    user: User,
    node_id: UUID,
) -> LadderExamGenerationResult:
    node, nodes, progress_by_node, progress = _get_node_and_progress(db, user=user, node_id=node_id)
    if _node_status(node, nodes, progress_by_node) == "locked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NODE_LOCKED)
    if not progress.material_completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_EXAM_REQUIRE_MATERIAL)
    if not progress.practice_completed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_EXAM_REQUIRE_PRACTICE)
    if progress.exam_passed:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_EXAM_ALREADY_PASSED)

    existing = get_latest_generated_attempt(db, user_id=user.id, node_id=node.id)
    if existing is not None:
        return LadderExamGenerationResult(attempt=_public_attempt(existing))

    ai_result = AIService(db).generate_ladder_exam(
        user=user,
        node_title=node.title,
        node_summary=node.summary,
        material=node.material_markdown,
        practice_items=node.practice_items,
    )
    attempt = create_exam_attempt(
        db,
        user_id=user.id,
        path_id=node.path_id,
        node_id=node.id,
        exam_payload=ai_result.payload.model_dump(mode="json"),
        model=ai_result.model,
        input_tokens=ai_result.usage.input_tokens,
        output_tokens=ai_result.usage.output_tokens,
    )
    return LadderExamGenerationResult(attempt=_public_attempt(attempt))


def get_ladder_exam(db: Session, *, user: User, attempt_id: UUID) -> LadderExamAttemptDetail:
    attempt = get_attempt_for_user(db, attempt_id=attempt_id, user_id=user.id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_EXAM_NOT_FOUND)
    return _public_attempt(attempt)


def submit_ladder_exam(
    db: Session,
    *,
    user: User,
    attempt_id: UUID,
    payload: LadderExamSubmitRequest,
) -> LadderExamSubmitResult:
    attempt = get_attempt_for_user(db, attempt_id=attempt_id, user_id=user.id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_EXAM_NOT_FOUND)
    if attempt.status == "submitted":
        ladder = _current_ladder_summary(db, user)
        return LadderExamSubmitResult(
            attempt=_public_attempt(attempt),
            score=attempt.score or 0,
            passed=attempt.passed,
            ladder=ladder,
        )

    answer_map: dict[str, str] = {}
    for answer in payload.answers:
        if answer.question_id in answer_map:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=LADDER_EXAM_VALIDATION_ERROR)
        answer_map[answer.question_id] = answer.option_id

    exam = LadderExamPayload.model_validate(attempt.exam_payload)
    question_ids = {question.id for question in exam.questions}
    if not set(answer_map).issubset(question_ids):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=LADDER_EXAM_VALIDATION_ERROR)
    results: list[LadderExamQuestionResult] = []
    score = 0
    for question in exam.questions:
        option_ids = {option.id for option in question.options}
        selected = answer_map.get(question.id)
        if selected is not None and selected not in option_ids:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=LADDER_EXAM_VALIDATION_ERROR)
        correct = selected == question.correct_option_id
        points = 20 if question.type == "code_reading" else 6
        if correct:
            score += points
        results.append(
            LadderExamQuestionResult(
                question_id=question.id,
                selected_option_id=selected,
                correct_option_id=question.correct_option_id,
                correct=correct,
                points=points if correct else 0,
                explanation=question.explanation,
            )
        )

    passed = score >= 80
    submitted = submit_exam_attempt(
        db,
        attempt=attempt,
        submitted_answers={"answers": [answer.model_dump(mode="json") for answer in payload.answers]},
        result_payload={"results": [result.model_dump(mode="json") for result in results]},
        score=score,
        passed=passed,
    )
    if passed:
        node = get_path_node_for_user(db, node_id=attempt.node_id, user_id=user.id)
        if node is not None:
            progress = get_progress_for_path(db, path=node.path, user_id=user.id).get(node.id)
            if progress is not None:
                mark_exam_passed(db, progress)

    ladder = _current_ladder_summary(db, user)
    refreshed = get_attempt_for_user(db, attempt_id=submitted.id, user_id=user.id) or submitted
    return LadderExamSubmitResult(
        attempt=_public_attempt(refreshed),
        score=score,
        passed=passed,
        ladder=ladder,
    )


def _current_ladder_summary(db: Session, user: User):
    path = get_active_path(db, user_id=user.id)
    if path is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=LADDER_PATH_CREATE_FAILED)
    return _to_summary(db, path, user_id=user.id)
