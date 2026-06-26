from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class LadderExamAttempt(Base):
    __tablename__ = "ladder_exam_attempts"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    path_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("learning_paths.id", ondelete="CASCADE"),
        index=True,
    )
    node_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("learning_path_nodes.id", ondelete="CASCADE"),
        index=True,
    )
    status: Mapped[str] = mapped_column(String(30), default="generated", index=True)
    exam_payload: Mapped[dict] = mapped_column(JSONB)
    submitted_answers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_type: Mapped[str] = mapped_column(String(80), default="ladder_exam_generation")
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    path = relationship("LearningPath")
    node = relationship("LearningPathNode")
