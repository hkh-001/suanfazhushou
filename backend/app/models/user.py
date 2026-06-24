from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    student_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(40), default="学生用户")
    current_level: Mapped[str] = mapped_column(String(40), default="beginner")
    goal_track: Mapped[str] = mapped_column(String(40), default="self_study")
    goal_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    learning_stage: Mapped[str] = mapped_column(String(80), default="beginner")
    target_track: Mapped[str] = mapped_column(String(80), default="algorithm_basics")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    learning_records = relationship("LearningRecord", back_populates="user")
    problems = relationship("Problem", back_populates="created_by_user")
    code_reviews = relationship("CodeReview", back_populates="user")
    mistake_notes = relationship("MistakeNote", back_populates="user")
