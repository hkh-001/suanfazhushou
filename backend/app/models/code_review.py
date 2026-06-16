from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class CodeReview(Base):
    __tablename__ = "code_reviews"
    __table_args__ = (
        CheckConstraint("language IN ('cpp', 'python')", name="ck_code_reviews_language"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    problem_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("problems.id", ondelete="SET NULL"), nullable=True)
    language: Mapped[str] = mapped_column(String(30))
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    code: Mapped[str] = mapped_column(Text)
    analysis_result: Mapped[str] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="code_reviews")
    topic = relationship("Topic", back_populates="code_reviews")
    problem = relationship("Problem", back_populates="code_reviews")
    mistake_notes = relationship("MistakeNote", back_populates="code_review")
