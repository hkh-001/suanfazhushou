from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ladder import LadderTemplate, LearningPath, LearningPathNode, NodeUserProgress
from app.models.topic import Topic


def get_default_template(
    db: Session,
    *,
    goal_track: str,
    current_level: str,
) -> LadderTemplate | None:
    stmt = (
        select(LadderTemplate)
        .where(
            LadderTemplate.goal_track == goal_track,
            LadderTemplate.current_level == current_level,
            LadderTemplate.is_default.is_(True),
        )
        .order_by(LadderTemplate.version.desc(), LadderTemplate.created_at.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def get_active_path(db: Session, *, user_id: UUID) -> LearningPath | None:
    stmt = (
        select(LearningPath)
        .options(
            selectinload(LearningPath.template),
            selectinload(LearningPath.nodes),
        )
        .where(LearningPath.user_id == user_id, LearningPath.status == "active")
    )
    return db.scalar(stmt)


def get_path_node_for_user(db: Session, *, node_id: UUID, user_id: UUID) -> LearningPathNode | None:
    stmt = (
        select(LearningPathNode)
        .join(LearningPath)
        .options(
            selectinload(LearningPathNode.path).selectinload(LearningPath.template),
            selectinload(LearningPathNode.path).selectinload(LearningPath.nodes),
        )
        .where(
            LearningPathNode.id == node_id,
            LearningPath.user_id == user_id,
            LearningPath.status == "active",
        )
    )
    return db.scalar(stmt)


def get_published_topic_by_slug(db: Session, *, slug: str) -> Topic | None:
    return db.scalar(select(Topic).where(Topic.slug == slug, Topic.status == "published"))


def create_path_with_nodes(
    db: Session,
    *,
    user_id: UUID,
    template: LadderTemplate,
    nodes: list[LearningPathNode],
) -> LearningPath:
    path = LearningPath(
        user_id=user_id,
        template_id=template.id,
        goal_track=template.goal_track,
        current_level=template.current_level,
        status="active",
    )
    db.add(path)
    db.flush()

    for node in nodes:
        node.path_id = path.id
        db.add(node)

    db.flush()

    for node in nodes:
        db.add(NodeUserProgress(user_id=user_id, node_id=node.id))

    db.commit()
    return get_active_path(db, user_id=user_id) or path


def get_progress_for_path(db: Session, *, path: LearningPath, user_id: UUID) -> dict[UUID, NodeUserProgress]:
    node_ids = [node.id for node in path.nodes]
    if not node_ids:
        return {}
    stmt = select(NodeUserProgress).where(
        NodeUserProgress.user_id == user_id,
        NodeUserProgress.node_id.in_(node_ids),
    )
    return {progress.node_id: progress for progress in db.scalars(stmt)}


def mark_material_completed(db: Session, progress: NodeUserProgress) -> None:
    if not progress.material_completed:
        progress.material_completed = True
        progress.material_completed_at = datetime.now(timezone.utc)
    db.commit()


def mark_practice_completed(db: Session, progress: NodeUserProgress) -> None:
    if not progress.practice_completed:
        progress.practice_completed = True
        progress.practice_completed_at = datetime.now(timezone.utc)
    db.commit()
