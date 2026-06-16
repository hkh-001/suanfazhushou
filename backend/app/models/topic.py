from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint("difficulty_score >= 1 AND difficulty_score <= 10", name="ck_topics_difficulty_score"),
        CheckConstraint("estimated_minutes > 0", name="ck_topics_estimated_minutes"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(120))
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    level: Mapped[str] = mapped_column(String(80))
    difficulty_score: Mapped[int] = mapped_column(Integer)
    summary: Mapped[str] = mapped_column(Text)
    content_markdown: Mapped[str] = mapped_column(Text)
    template_code_cpp: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_code_python: Mapped[str | None] = mapped_column(Text, nullable=True)
    complexity_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_pitfalls: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    parent = relationship("Topic", remote_side=[id])
    learning_records = relationship("LearningRecord", back_populates="topic")
    problem_tags = relationship("ProblemTag", back_populates="topic")
    code_reviews = relationship("CodeReview", back_populates="topic")
    mistake_notes = relationship("MistakeNote", back_populates="topic")


class TopicDependency(Base):
    __tablename__ = "topic_dependencies"
    __table_args__ = (
        UniqueConstraint("topic_id", "depends_on_topic_id", name="uq_topic_dependencies_pair"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    topic_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"))
    depends_on_topic_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
