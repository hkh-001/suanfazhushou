from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (
        UniqueConstraint("created_by_user_id", "slug", name="uq_problems_user_slug"),
        CheckConstraint(
            "difficulty IN ('beginner', 'basic', 'intermediate', 'advanced')",
            name="ck_problems_difficulty",
        ),
        CheckConstraint("estimated_minutes IS NULL OR estimated_minutes > 0", name="ck_problems_estimated_minutes"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(180))
    source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(30))
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description_markdown: Mapped[str] = mapped_column(Text)
    input_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_code_cpp: Mapped[str | None] = mapped_column(Text, nullable=True)
    solution_code_python: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by_user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    created_by_user = relationship("User", back_populates="problems")
    problem_tags = relationship("ProblemTag", back_populates="problem", cascade="all, delete-orphan")


class ProblemTag(Base):
    __tablename__ = "problem_tags"
    __table_args__ = (
        UniqueConstraint("problem_id", "topic_id", name="uq_problem_tags_problem_topic"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    problem_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("problems.id", ondelete="CASCADE"))
    topic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    problem = relationship("Problem", back_populates="problem_tags")
    topic = relationship("Topic", back_populates="problem_tags")
