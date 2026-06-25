from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class LadderTemplate(Base):
    __tablename__ = "ladder_templates"
    __table_args__ = (
        UniqueConstraint("goal_track", "current_level", "version", name="uq_ladder_templates_track_level_version"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    goal_track: Mapped[str] = mapped_column(String(40), index=True)
    current_level: Mapped[str] = mapped_column(String(40), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_data: Mapped[dict] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    learning_paths = relationship("LearningPath", back_populates="template")


class LearningPath(Base):
    __tablename__ = "learning_paths"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    template_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("ladder_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    goal_track: Mapped[str] = mapped_column(String(40))
    current_level: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    template = relationship("LadderTemplate", back_populates="learning_paths")
    nodes = relationship(
        "LearningPathNode",
        back_populates="path",
        cascade="all, delete-orphan",
        order_by="LearningPathNode.node_index",
    )


class LearningPathNode(Base):
    __tablename__ = "learning_path_nodes"
    __table_args__ = (
        UniqueConstraint("path_id", "phase_index", "node_index", name="uq_learning_path_nodes_path_phase_node"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    path_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("learning_paths.id", ondelete="CASCADE"))
    topic_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    phase_index: Mapped[int] = mapped_column(Integer)
    node_index: Mapped[int] = mapped_column(Integer)
    algorithm_key: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(120))
    summary: Mapped[str] = mapped_column(Text)
    material_markdown: Mapped[str] = mapped_column(Text)
    resource_links: Mapped[list] = mapped_column(JSONB, default=list)
    unlock_rule: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    path = relationship("LearningPath", back_populates="nodes")
    topic = relationship("Topic")
    progress_entries = relationship("NodeUserProgress", back_populates="node", cascade="all, delete-orphan")


class NodeUserProgress(Base):
    __tablename__ = "node_user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "node_id", name="uq_node_user_progress_user_node"),
    )

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    node_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), ForeignKey("learning_path_nodes.id", ondelete="CASCADE"))
    material_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    practice_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    exam_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    material_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    practice_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exam_passed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    node = relationship("LearningPathNode", back_populates="progress_entries")
    user = relationship("User")
