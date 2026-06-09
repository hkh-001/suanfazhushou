from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_learning_records_user_topic"),
        CheckConstraint("progress_percent >= 0 AND progress_percent <= 100", name="ck_learning_progress_percent"),
        CheckConstraint("mastery_level >= 0 AND mastery_level <= 5", name="ck_learning_mastery_level"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(30), default="not_started")
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    mastery_level: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_studied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="learning_records")
    topic = relationship("Topic", back_populates="learning_records")
