import re
from math import ceil
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.problem import Problem
from app.models.test_case import TestCase
from app.models.topic import Topic
from app.models.user import User
from app.repositories.problems import (
    allocate_problem_display_id,
    count_public_problems,
    count_user_problems,
    create_problem as insert_problem,
    delete_problem as remove_problem,
    get_problem_by_id,
    get_problem_by_slug,
    get_published_topics_by_ids,
    get_public_problem as get_public_problem_record,
    get_user_problem,
    list_public_problems,
    list_user_problems,
    replace_problem_tags,
)
from app.schemas.common import PaginatedResponse, Pagination
from app.schemas.problem import (
    GeneratedProblemSaveRequest,
    ProblemCreate,
    ProblemDeleteResult,
    ProblemDetail,
    ProblemListItem,
    ProblemModelData,
    ProblemTopicTag,
    ProblemUpdate,
)

PROBLEM_NOT_FOUND = {"code": "PROBLEM_NOT_FOUND", "message": "Problem not found"}
PROBLEM_SLUG_EXISTS = {"code": "PROBLEM_SLUG_ALREADY_EXISTS", "message": "Problem slug already exists"}
TOPIC_NOT_FOUND = {"code": "TOPIC_NOT_FOUND", "message": "Topic not found"}
VALIDATION_ERROR = {"code": "VALIDATION_ERROR", "message": "Request validation failed"}
PUBLIC_PROBLEM_FORBIDDEN = {
    "code": "PUBLIC_PROBLEM_FORBIDDEN",
    "message": "Only admins can create or modify public problems",
}


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROBLEM_NOT_FOUND)


def _normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return re.sub(r"-+", "-", slug).strip("-")


def _dedupe_topic_ids(topic_ids: list[UUID] | None) -> list[UUID]:
    if not topic_ids:
        return []
    return list(dict.fromkeys(topic_ids))


def _resolve_topics(db: Session, topic_ids: list[UUID] | None) -> list[Topic]:
    deduped_ids = _dedupe_topic_ids(topic_ids)
    topics = get_published_topics_by_ids(db, deduped_ids)
    if len(topics) != len(deduped_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=TOPIC_NOT_FOUND)
    return topics


def _ensure_slug_available(
    db: Session,
    *,
    user_id: UUID,
    slug: str,
    exclude_problem_id: UUID | None = None,
) -> None:
    if get_problem_by_slug(db, user_id=user_id, slug=slug, exclude_problem_id=exclude_problem_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=PROBLEM_SLUG_EXISTS)


def _validation_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=VALIDATION_ERROR)


def _public_forbidden() -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=PUBLIC_PROBLEM_FORBIDDEN)


def _is_admin(user: User) -> bool:
    return user.role == "admin"


def _can_edit(problem: Problem, user: User) -> bool:
    if problem.is_public:
        return _is_admin(user)
    return problem.created_by_user_id == user.id


def _generate_slug(db: Session, *, user_id: UUID, title: str) -> str:
    base_slug = _normalize_slug(title) or f"problem-{uuid4().hex[:8]}"
    candidate = base_slug
    suffix = 2
    while get_problem_by_slug(db, user_id=user_id, slug=candidate) is not None:
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


def _problem_topics(problem: Problem) -> list[ProblemTopicTag]:
    return [
        ProblemTopicTag(
            id=tag.topic.id,
            title=tag.topic.title,
            slug=tag.topic.slug,
            category=tag.topic.category,
        )
        for tag in problem.problem_tags
        if tag.topic is not None
    ]


def _to_list_item(problem: Problem, user: User) -> ProblemListItem:
    data = ProblemModelData.model_validate(problem).model_dump()
    data.pop("description_markdown")
    for key in (
        "input_format",
        "output_format",
        "constraints",
        "sample_input",
        "sample_output",
        "hint",
        "solution_markdown",
        "solution_code_cpp",
        "solution_code_python",
        "published_at",
    ):
        data.pop(key)
    can_edit = _can_edit(problem, user)
    return ProblemListItem(**data, topic_tags=_problem_topics(problem), can_edit=can_edit, can_delete=can_edit)


def _to_detail(problem: Problem, user: User) -> ProblemDetail:
    data = ProblemModelData.model_validate(problem).model_dump()
    can_edit = _can_edit(problem, user)
    return ProblemDetail(**data, topic_tags=_problem_topics(problem), can_edit=can_edit, can_delete=can_edit)


def list_problems(db: Session, *, user: User, page: int, page_size: int) -> PaginatedResponse[ProblemListItem]:
    total = count_user_problems(db, user_id=user.id)
    problems = list_user_problems(db, user_id=user.id, page=page, page_size=page_size)
    return PaginatedResponse(
        data=[_to_list_item(problem, user) for problem in problems],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        ),
    )


def list_public_problem_bank(db: Session, *, user: User, page: int, page_size: int) -> PaginatedResponse[ProblemListItem]:
    total = count_public_problems(db)
    problems = list_public_problems(db, page=page, page_size=page_size)
    return PaginatedResponse(
        data=[_to_list_item(problem, user) for problem in problems],
        pagination=Pagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        ),
    )


def get_problem(db: Session, *, user: User, problem_id: UUID) -> ProblemDetail:
    problem = get_user_problem(db, problem_id=problem_id, user_id=user.id)
    if problem is None:
        problem = get_public_problem_record(db, problem_id=problem_id)
    if problem is None:
        raise _not_found()
    return _to_detail(problem, user)


def get_public_problem(db: Session, *, user: User, problem_id: UUID) -> ProblemDetail:
    problem = get_public_problem_record(db, problem_id=problem_id)
    if problem is None:
        raise _not_found()
    return _to_detail(problem, user)


def create_problem(db: Session, *, user: User, payload: ProblemCreate) -> ProblemDetail:
    if payload.is_public and not _is_admin(user):
        raise _public_forbidden()

    if payload.slug is None:
        slug = _generate_slug(db, user_id=user.id, title=payload.title)
    else:
        slug = _normalize_slug(payload.slug)
        if not slug:
            raise _validation_error()
        _ensure_slug_available(db, user_id=user.id, slug=slug)

    topics = _resolve_topics(db, payload.topic_ids)
    problem = Problem(
        display_id=allocate_problem_display_id(db, user_id=user.id),
        title=payload.title,
        slug=slug,
        source=payload.source,
        source_url=payload.source_url,
        difficulty=payload.difficulty,
        estimated_minutes=payload.estimated_minutes,
        description_markdown=payload.description_markdown,
        input_format=payload.input_format,
        output_format=payload.output_format,
        constraints=payload.constraints,
        sample_input=payload.sample_input,
        sample_output=payload.sample_output,
        hint=payload.hint,
        solution_markdown=payload.solution_markdown,
        solution_code_cpp=payload.solution_code_cpp,
        solution_code_python=payload.solution_code_python,
        is_ai_generated=False,
        is_published=False,
        is_public=payload.is_public,
        created_by_user_id=user.id,
    )
    return _to_detail(insert_problem(db, problem, topics), user)


def save_ai_generated_problem(db: Session, *, user: User, payload: GeneratedProblemSaveRequest) -> ProblemDetail:
    topics = _resolve_topics(db, [payload.topic_id] if payload.topic_id else [])
    hint = "\n".join(f"- {hint}" for hint in payload.hints) or None
    sample_case = next((case for case in payload.test_cases if case.is_sample), payload.test_cases[0])
    problem = Problem(
        display_id=allocate_problem_display_id(db, user_id=user.id),
        title=payload.title,
        slug=_generate_slug(db, user_id=user.id, title=payload.title),
        source="ai_generated",
        source_url=None,
        difficulty=payload.difficulty,
        estimated_minutes=None,
        description_markdown=payload.statement,
        input_format=payload.input_format,
        output_format=payload.output_format,
        constraints=payload.constraints,
        sample_input=payload.sample_input or sample_case.input,
        sample_output=payload.sample_output or sample_case.expected_output,
        hint=hint,
        solution_markdown=payload.solution_idea,
        solution_code_cpp=None,
        solution_code_python=None,
        is_ai_generated=True,
        is_published=False,
        is_public=False,
        created_by_user_id=user.id,
    )
    test_cases = [
        TestCase(
            case_index=index,
            name=case.name or f"{index:02d}",
            input_text=case.input,
            expected_output_text=case.expected_output,
            is_sample=case.is_sample or index == 1,
            is_hidden=False,
        )
        for index, case in enumerate(payload.test_cases, start=1)
    ]
    return _to_detail(insert_problem(db, problem, topics, test_cases=test_cases), user)


def update_problem(db: Session, *, user: User, problem_id: UUID, payload: ProblemUpdate) -> ProblemDetail:
    problem = get_problem_by_id(db, problem_id=problem_id)
    if problem is None:
        raise _not_found()
    if problem.is_public:
        if not _is_admin(user):
            raise _not_found()
    elif problem.created_by_user_id != user.id:
        raise _not_found()

    fields = payload.model_fields_set
    if "is_public" in fields:
        requested_public = bool(payload.is_public)
        if problem.is_public and not requested_public:
            raise _public_forbidden()
        if requested_public and not problem.is_public:
            if not _is_admin(user) or problem.created_by_user_id != user.id:
                raise _public_forbidden()
            problem.is_public = True
        elif requested_public:
            problem.is_public = True

    if "slug" in fields:
        slug = _normalize_slug(payload.slug or "")
        if not slug:
            raise _validation_error()
        _ensure_slug_available(db, user_id=problem.created_by_user_id, slug=slug, exclude_problem_id=problem.id)
        problem.slug = slug

    for required_field in ("title", "difficulty", "description_markdown"):
        if required_field in fields and getattr(payload, required_field) is None:
            raise _validation_error()

    for field in (
        "title",
        "source",
        "source_url",
        "difficulty",
        "estimated_minutes",
        "description_markdown",
        "input_format",
        "output_format",
        "constraints",
        "sample_input",
        "sample_output",
        "hint",
        "solution_markdown",
        "solution_code_cpp",
        "solution_code_python",
    ):
        if field in fields:
            setattr(problem, field, getattr(payload, field))

    if "topic_ids" in fields:
        topics = _resolve_topics(db, payload.topic_ids)
        replace_problem_tags(db, problem=problem, topics=topics)

    db.commit()
    refreshed = get_problem_by_id(db, problem_id=problem.id)
    if refreshed is None:
        raise _not_found()
    return _to_detail(refreshed, user)


def delete_problem(db: Session, *, user: User, problem_id: UUID) -> ProblemDeleteResult:
    problem = get_problem_by_id(db, problem_id=problem_id)
    if problem is None:
        raise _not_found()
    if problem.is_public:
        if not _is_admin(user):
            raise _not_found()
    elif problem.created_by_user_id != user.id:
        raise _not_found()
    remove_problem(db, problem)
    return ProblemDeleteResult(success=True)
