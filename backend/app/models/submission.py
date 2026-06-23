from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


SUBMISSION_VERDICTS = (
    "accepted",
    "wrong_answer",
    "compile_error",
    "runtime_error",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "output_limit_exceeded",
    "internal_error",
)

CASE_VERDICTS = (
    "accepted",
    "wrong_answer",
    "runtime_error",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "output_limit_exceeded",
    "not_run",
)


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        CheckConstraint("language IN ('cpp', 'python')", name="ck_submissions_language"),
        CheckConstraint(
            f"verdict IN {SUBMISSION_VERDICTS}",
            name="ck_submissions_verdict",
        ),
        CheckConstraint("passed_case_count >= 0", name="ck_submissions_passed_case_count"),
        CheckConstraint("total_case_count > 0", name="ck_submissions_total_case_count"),
        CheckConstraint(
            "passed_case_count <= total_case_count",
            name="ck_submissions_passed_not_above_total",
        ),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    problem_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("problems.id", ondelete="SET NULL"),
        nullable=True,
    )
    problem_title: Mapped[str] = mapped_column(String(160))
    problem_display_id: Mapped[int] = mapped_column(Integer)
    language: Mapped[str] = mapped_column(String(20))
    source_code: Mapped[str] = mapped_column(Text)
    verdict: Mapped[str] = mapped_column(String(40))
    passed_case_count: Mapped[int] = mapped_column(Integer, default=0)
    total_case_count: Mapped[int] = mapped_column(Integer)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    compile_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    user = relationship("User")
    problem = relationship("Problem")
    case_results = relationship(
        "SubmissionCaseResult",
        back_populates="submission",
        cascade="all, delete-orphan",
        order_by="SubmissionCaseResult.case_index",
    )


class SubmissionCaseResult(Base):
    __tablename__ = "submission_case_results"
    __table_args__ = (
        UniqueConstraint("submission_id", "case_index", name="uq_submission_case_results_submission_case"),
        CheckConstraint(f"verdict IN {CASE_VERDICTS}", name="ck_submission_case_results_verdict"),
        CheckConstraint("case_index > 0", name="ck_submission_case_results_case_index"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
    )
    test_case_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("test_cases.id", ondelete="SET NULL"),
        nullable=True,
    )
    case_index: Mapped[int] = mapped_column(Integer)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean)
    verdict: Mapped[str] = mapped_column(String(40))
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("Submission", back_populates="case_results")
    test_case = relationship("TestCase")
