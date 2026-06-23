from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.submission import Submission, SubmissionCaseResult


def create_submission(
    db: Session,
    *,
    submission: Submission,
    case_results: list[SubmissionCaseResult],
) -> Submission:
    db.add(submission)
    db.flush()
    for case_result in case_results:
        case_result.submission_id = submission.id
        db.add(case_result)
    db.commit()
    return get_user_submission(db, submission_id=submission.id, user_id=submission.user_id) or submission


def get_user_submission(db: Session, *, submission_id: UUID, user_id: UUID) -> Submission | None:
    stmt = (
        select(Submission)
        .options(
            selectinload(Submission.case_results),
            selectinload(Submission.problem),
        )
        .where(Submission.id == submission_id, Submission.user_id == user_id)
    )
    return db.scalar(stmt)
