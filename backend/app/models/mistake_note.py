from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class MistakeNote(Base):
    __tablename__ = "mistake_notes"
    __table_args__ = (
        CheckConstraint(
            "review_status IN ('open', 'reviewing', 'resolved')",
            name="ck_mistake_notes_review_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    problem_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("problems.id", ondelete="SET NULL"), nullable=True)
    topic_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True)
    code_review_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("code_reviews.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(160))
    error_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    root_cause: Mapped[str] = mapped_column(Text)
    wrong_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    fixed_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    fix_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_reflection: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_status: Mapped[str] = mapped_column(String(30), default="open")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="mistake_notes")
    topic = relationship("Topic", back_populates="mistake_notes")
    problem = relationship("Problem", back_populates="mistake_notes")
    code_review = relationship("CodeReview", back_populates="mistake_notes")
