from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        UniqueConstraint("problem_id", "case_index", name="uq_test_cases_problem_case_index"),
        CheckConstraint("case_index > 0", name="ck_test_cases_case_index_positive"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    problem_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"))
    case_index: Mapped[int] = mapped_column(Integer)
    name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    input_text: Mapped[str] = mapped_column(Text)
    expected_output_text: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(Boolean, default=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    problem = relationship("Problem", back_populates="test_cases")
