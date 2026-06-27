from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.interactive_lesson import InteractiveLesson
from app.models.ladder import LearningPathNode, NodeUserProgress
from app.models.topic import Topic
from app.models.user import User
from app.repositories.interactive_lessons import (
    create_pending_node_lesson,
    create_pending_topic_lesson,
    get_lesson_for_user,
    get_recent_reusable_node_lesson,
    get_recent_reusable_topic_lesson,
    mark_lesson_failed,
    update_lesson_status,
)
from app.repositories.ladder import get_path_node_for_user, get_progress_for_path
from app.repositories.topics import get_published_topic
from app.schemas.interactive_lesson import InteractiveLessonDetail
from app.schemas.openmaic import OpenMAICGeneratePayload, OpenMAICJobStatus
from app.services.ladder import LADDER_NODE_NOT_FOUND, NODE_LOCKED, _node_status
from app.services.openmaic import HttpOpenMAICClient, OpenMAICClient, OpenMAICClientError

SAFE_OPENMAIC_ERROR_MESSAGES = {
    "OPENMAIC_CONFIG_MISSING": "互动课堂服务配置缺失，请稍后再试。",
    "OPENMAIC_TIMEOUT": "互动课堂服务请求超时，请稍后重试。",
    "OPENMAIC_UNAVAILABLE": "互动课堂服务暂不可用，请稍后重试。",
    "OPENMAIC_INVALID_RESPONSE": "互动课堂服务返回了无法识别的结果，请稍后重试。",
    "OPENMAIC_JOB_NOT_FOUND": "互动课堂任务不存在或已过期，请重新生成。",
}
DEFAULT_OPENMAIC_ERROR_MESSAGE = "互动课堂服务暂不可用，请稍后重试。"


def get_openmaic_client() -> OpenMAICClient:
    return HttpOpenMAICClient()


def _feature_guard() -> None:
    if not settings.enable_openmaic_integration:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FEATURE_DISABLED", "message": "OpenMAIC integration is disabled"},
        )


def _topic_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "TOPIC_NOT_FOUND", "message": "Topic not found"},
    )


def _lesson_not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "INTERACTIVE_LESSON_NOT_FOUND", "message": "Interactive lesson not found"},
    )


def _handle_openmaic_error(exc: OpenMAICClientError) -> HTTPException:
    return HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": _safe_error_message(exc.code)},
    )


def _safe_error_message(code: str) -> str:
    return SAFE_OPENMAIC_ERROR_MESSAGES.get(code, DEFAULT_OPENMAIC_ERROR_MESSAGE)


def _truncate(value: str, limit: int) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return f"{text[: limit - 20]}\n...[内容已截断]"


def _topic_lesson_title(topic: Topic) -> str:
    return f"{topic.title.strip()} 互动课堂"[:160]


def _node_lesson_title(node: LearningPathNode) -> str:
    return f"{node.title.strip()} 互动课堂"[:160]


def _build_topic_requirement(*, topic: Topic, user: User) -> str:
    level = user.current_level or "beginner"
    goal = user.goal_track or "self_study"
    content_excerpt = _truncate(topic.content_markdown or "", 900)
    requirement = f"""请生成一节中文互动算法课堂。

知识点标题：{topic.title}
知识点分类：{topic.category}
知识点阶段：{topic.level}
知识点摘要：{topic.summary}
学习者当前水平：{level}
学习目标方向：{goal}

安全与边界：
- 不包含学号、完整学习历史、提交代码、隐藏测试、考试答案键或私人笔记。
- 不要求运行代码，不生成需要外部判题的任务。
- 只围绕上面的知识点生成课堂。

知识点内容摘录：
{content_excerpt}

课堂要求：
1. 使用中文讲解，先解释概念，再给出推导过程和常见误区。
2. 面向算法学习场景，包含互动提问、小测验和可视化演示建议。
"""
    return _truncate(requirement, 2000)


def _build_node_requirement(*, node: LearningPathNode, progress: NodeUserProgress | None, user: User) -> str:
    level = user.current_level or "beginner"
    goal = user.goal_track or "self_study"
    material_excerpt = _truncate(node.material_markdown or "", 900)
    material_completed = bool(progress and progress.material_completed)
    practice_completed = bool(progress and progress.practice_completed)
    exam_passed = bool(progress and progress.exam_passed)
    requirement = f"""请生成一节中文互动算法课堂。

来源：学习天梯节点
节点标题：{node.title}
节点摘要：{node.summary}
阶段序号：{node.phase_index}
节点序号：{node.node_index}
学习者当前水平：{level}
学习目标方向：{goal}
资料阅读完成：{material_completed}
节点练习完成：{practice_completed}
节点考试通过：{exam_passed}

安全与边界：
- 不包含学号、完整学习历史、提交代码、隐藏测试、考试题目、考试答案键或练习答案键。
- 不包含任何练习题原始配置、选项答案字段或完整考试数据。
- 不要求运行代码，不生成需要外部判题的任务。
- 只围绕当前节点资料生成课堂。

节点资料摘录：
{material_excerpt}

课堂要求：
1. 使用中文讲解，面向当前天梯节点做概念讲解、步骤拆解和常见误区提醒。
2. 结合学习者完成状态，给出适合继续学习的互动提问和小测验。
3. 不修改学习进度，不声明用户已完成资料、练习或考试。
"""
    return _truncate(requirement, 2000)


def _status_from_openmaic(result: OpenMAICJobStatus) -> str:
    if result.status == "completed":
        return "completed" if result.classroom_url else "processing"
    if result.status == "failed":
        return "failed"
    if result.status in {"pending", "submitted", "processing"}:
        return result.status
    return "processing"


def _apply_openmaic_result(db: Session, *, lesson: InteractiveLesson, result: OpenMAICJobStatus) -> InteractiveLesson:
    mapped_status = _status_from_openmaic(result)
    error_code = None
    error_message = None
    if mapped_status == "failed":
        error_code = "INTERACTIVE_LESSON_GENERATION_FAILED"
        error_message = "互动课堂生成失败，请稍后重试。"
    return update_lesson_status(
        db,
        lesson=lesson,
        status=mapped_status,
        job_id=result.job_id or lesson.openmaic_job_id,
        poll_url=result.poll_url or lesson.openmaic_poll_url,
        classroom_url=result.classroom_url if mapped_status == "completed" else None,
        error_code=error_code,
        error_message=error_message,
    )


def _to_detail(lesson: InteractiveLesson) -> InteractiveLessonDetail:
    return InteractiveLessonDetail(
        id=lesson.id,
        source_type=lesson.source_type,
        topic_id=lesson.topic_id,
        node_id=lesson.node_id,
        provider=lesson.provider,
        status=lesson.status,
        title=lesson.title,
        classroom_url=lesson.openmaic_classroom_url if lesson.status == "completed" else None,
        error_code=lesson.error_code,
        error_message=lesson.error_message,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
        completed_at=lesson.completed_at,
    )


async def _generate_lesson(
    db: Session,
    *,
    lesson: InteractiveLesson,
    requirement: str,
    client: OpenMAICClient | None,
) -> InteractiveLessonDetail:
    openmaic_client = client or get_openmaic_client()
    try:
        result = await openmaic_client.generate_classroom(OpenMAICGeneratePayload(requirement=requirement))
    except OpenMAICClientError as exc:
        mark_lesson_failed(
            db,
            lesson=lesson,
            error_code=exc.code,
            error_message=_safe_error_message(exc.code),
        )
        raise _handle_openmaic_error(exc) from exc

    lesson = _apply_openmaic_result(db, lesson=lesson, result=result)
    return _to_detail(lesson)


async def create_topic_interactive_lesson(
    db: Session,
    *,
    topic_id: UUID,
    user: User,
    client: OpenMAICClient | None = None,
) -> InteractiveLessonDetail:
    _feature_guard()
    topic = get_published_topic(db, topic_id)
    if topic is None:
        raise _topic_not_found()

    reusable = get_recent_reusable_topic_lesson(db, user_id=user.id, topic_id=topic.id)
    if reusable is not None:
        return _to_detail(reusable)

    lesson = create_pending_topic_lesson(db, user_id=user.id, topic_id=topic.id, title=_topic_lesson_title(topic))
    return await _generate_lesson(
        db,
        lesson=lesson,
        requirement=_build_topic_requirement(topic=topic, user=user),
        client=client,
    )


async def create_ladder_node_interactive_lesson(
    db: Session,
    *,
    node_id: UUID,
    user: User,
    client: OpenMAICClient | None = None,
) -> InteractiveLessonDetail:
    _feature_guard()
    node = get_path_node_for_user(db, node_id=node_id, user_id=user.id)
    if node is None or node.path.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=LADDER_NODE_NOT_FOUND)

    nodes = sorted(node.path.nodes, key=lambda item: item.node_index)
    progress_by_node = get_progress_for_path(db, path=node.path, user_id=user.id)
    if _node_status(node, nodes, progress_by_node) == "locked":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=NODE_LOCKED)

    reusable = get_recent_reusable_node_lesson(db, user_id=user.id, node_id=node.id)
    if reusable is not None:
        return _to_detail(reusable)

    lesson = create_pending_node_lesson(db, user_id=user.id, node_id=node.id, title=_node_lesson_title(node))
    return await _generate_lesson(
        db,
        lesson=lesson,
        requirement=_build_node_requirement(node=node, progress=progress_by_node.get(node.id), user=user),
        client=client,
    )


def get_interactive_lesson(db: Session, *, lesson_id: UUID, user: User) -> InteractiveLessonDetail:
    lesson = get_lesson_for_user(db, lesson_id=lesson_id, user_id=user.id)
    if lesson is None:
        raise _lesson_not_found()
    return _to_detail(lesson)


async def refresh_interactive_lesson(
    db: Session,
    *,
    lesson_id: UUID,
    user: User,
    client: OpenMAICClient | None = None,
) -> InteractiveLessonDetail:
    _feature_guard()
    lesson = get_lesson_for_user(db, lesson_id=lesson_id, user_id=user.id)
    if lesson is None:
        raise _lesson_not_found()
    if lesson.openmaic_job_id is None or lesson.status in {"completed", "failed"}:
        return _to_detail(lesson)

    openmaic_client = client or get_openmaic_client()
    try:
        result = await openmaic_client.get_job(lesson.openmaic_job_id)
    except OpenMAICClientError as exc:
        lesson = mark_lesson_failed(
            db,
            lesson=lesson,
            error_code=exc.code,
            error_message=_safe_error_message(exc.code),
        )
        return _to_detail(lesson)

    lesson = _apply_openmaic_result(db, lesson=lesson, result=result)
    return _to_detail(lesson)
