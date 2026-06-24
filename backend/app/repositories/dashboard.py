from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload

from app.models.learning_record import LearningRecord
from app.models.mistake_note import MistakeNote
from app.models.problem import Problem, ProblemTag
from app.models.submission import Submission
from app.models.topic import Topic


DashboardTopicRow = tuple[Topic, LearningRecord | None]


def get_dashboard_topic_rows(db: Session, *, user_id: UUID) -> list[DashboardTopicRow]:
    statement = (
        select(Topic, LearningRecord)
        .outerjoin(
            LearningRecord,
            and_(
                LearningRecord.topic_id == Topic.id,
                LearningRecord.user_id == user_id,
            ),
        )
        .where(Topic.status == "published")
        .order_by(Topic.category.asc(), Topic.order_index.asc(), Topic.created_at.asc())
    )
    return list(db.execute(statement).all())


def get_dashboard_open_mistakes(db: Session, *, user_id: UUID) -> list[MistakeNote]:
    statement = (
        select(MistakeNote)
        .options(
            selectinload(MistakeNote.topic),
            selectinload(MistakeNote.problem).selectinload(Problem.problem_tags).selectinload(ProblemTag.topic),
        )
        .where(
            MistakeNote.user_id == user_id,
            MistakeNote.review_status.in_(("open", "reviewing")),
        )
        .order_by(MistakeNote.created_at.desc(), MistakeNote.id.desc())
    )
    return list(db.scalars(statement).all())


def get_dashboard_failed_submissions(db: Session, *, user_id: UUID) -> list[Submission]:
    statement = (
        select(Submission)
        .options(
            selectinload(Submission.problem).selectinload(Problem.problem_tags).selectinload(ProblemTag.topic),
        )
        .where(
            Submission.user_id == user_id,
            Submission.verdict.notin_(("accepted", "internal_error")),
            Submission.problem_id.is_not(None),
        )
        .order_by(Submission.created_at.desc(), Submission.id.desc())
    )
    return list(db.scalars(statement).all())


def get_dashboard_user_problems(db: Session, *, user_id: UUID) -> list[Problem]:
    statement = (
        select(Problem)
        .options(selectinload(Problem.problem_tags).selectinload(ProblemTag.topic))
        .where(Problem.created_by_user_id == user_id)
        .order_by(Problem.created_at.desc(), Problem.id.desc())
    )
    return list(db.scalars(statement).all())


def get_dashboard_accepted_problem_ids(db: Session, *, user_id: UUID) -> set[UUID]:
    statement = select(Submission.problem_id).where(
        Submission.user_id == user_id,
        Submission.verdict == "accepted",
        Submission.problem_id.is_not(None),
    )
    return {problem_id for problem_id in db.scalars(statement).all() if problem_id is not None}
