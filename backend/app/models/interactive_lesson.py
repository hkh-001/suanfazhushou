from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class InteractiveLesson(Base):
    __tablename__ = "interactive_lessons"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    node_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("learning_path_nodes.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(30), default="topic")
    provider: Mapped[str] = mapped_column(String(40), default="openmaic")
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    title: Mapped[str] = mapped_column(String(160))
    openmaic_job_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    openmaic_poll_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    openmaic_classroom_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    topic = relationship("Topic")
    node = relationship("LearningPathNode")
