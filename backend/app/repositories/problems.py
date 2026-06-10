from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.problem import Problem, ProblemTag
from app.models.topic import Topic


def count_user_problems(db: Session, *, user_id: UUID) -> int:
    return db.scalar(select(func.count()).select_from(Problem).where(Problem.created_by_user_id == user_id)) or 0


def list_user_problems(db: Session, *, user_id: UUID, page: int, page_size: int) -> list[Problem]:
    offset = (page - 1) * page_size
    stmt = (
        select(Problem)
        .options(selectinload(Problem.problem_tags).selectinload(ProblemTag.topic))
        .where(Problem.created_by_user_id == user_id)
        .order_by(Problem.created_at.desc(), Problem.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    return list(db.scalars(stmt).all())


def get_user_problem(db: Session, *, problem_id: UUID, user_id: UUID) -> Problem | None:
    stmt = (
        select(Problem)
        .options(selectinload(Problem.problem_tags).selectinload(ProblemTag.topic))
        .where(Problem.id == problem_id, Problem.created_by_user_id == user_id)
    )
    return db.scalar(stmt)


def get_problem_by_slug(
    db: Session,
    *,
    user_id: UUID,
    slug: str,
    exclude_problem_id: UUID | None = None,
) -> Problem | None:
    stmt = select(Problem).where(Problem.created_by_user_id == user_id, Problem.slug == slug)
    if exclude_problem_id is not None:
        stmt = stmt.where(Problem.id != exclude_problem_id)
    return db.scalar(stmt)


def get_published_topics_by_ids(db: Session, topic_ids: list[UUID]) -> list[Topic]:
    if not topic_ids:
        return []
    stmt = select(Topic).where(Topic.id.in_(topic_ids), Topic.status == "published")
    return list(db.scalars(stmt).all())


def create_problem(db: Session, problem: Problem, topics: list[Topic]) -> Problem:
    db.add(problem)
    db.flush()
    replace_problem_tags(db, problem=problem, topics=topics)
    db.commit()
    db.refresh(problem)
    return get_user_problem(db, problem_id=problem.id, user_id=problem.created_by_user_id) or problem


def replace_problem_tags(db: Session, *, problem: Problem, topics: list[Topic]) -> None:
    problem.problem_tags.clear()
    for topic in topics:
        problem.problem_tags.append(ProblemTag(topic_id=topic.id))
    db.flush()


def delete_problem(db: Session, problem: Problem) -> None:
    db.delete(problem)
    db.commit()
