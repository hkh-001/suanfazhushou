from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ladder import LearningPath, LearningPathNode, NodeUserProgress
from app.models.ladder_exam import LadderExamAttempt
from app.models.learning_record import LearningRecord
from app.models.mistake_note import MistakeNote
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.topic import Topic
from app.repositories.dashboard import (
    get_dashboard_accepted_problem_ids,
    get_dashboard_active_ladder_path,
    get_dashboard_failed_submissions,
    get_dashboard_latest_ladder_attempts,
    get_dashboard_open_mistakes,
    get_dashboard_topic_rows,
    get_dashboard_user_problems,
)
from app.repositories.ladder import get_progress_for_path
from app.schemas.dashboard import (
    DashboardActivityItem,
    DashboardCategoryProgress,
    DashboardLadderProgress,
    DashboardNextStep,
    DashboardPracticeRecommendation,
    DashboardPracticeTopicTag,
    DashboardRecommendationAction,
    DashboardReviewItem,
    DashboardStatusCount,
    DashboardSummary,
    DashboardWeakTopic,
)
from app.services.ladder import _node_status


STALE_LEARNING_DAYS = 7
FAILED_VERDICTS = {
    "wrong_answer",
    "compile_error",
    "runtime_error",
    "time_limit_exceeded",
    "memory_limit_exceeded",
    "output_limit_exceeded",
}


@dataclass
class WeakTopicAccumulator:
    topic: Topic
    learning_score: int = 0
    open_mistake_count: int = 0
    failed_submission_count: int = 0
    stale_learning_bonus: int = 0
    signals: set[str] = field(default_factory=set)


def _percent(count: int, total: int) -> int:
    return round((count / total) * 100) if total else 0


def _is_started(record: LearningRecord | None) -> bool:
    return record is not None and record.status in {"learning", "mastered"}


def _is_mastered(record: LearningRecord | None) -> bool:
    return record is not None and record.status == "mastered"


def _is_learning(record: LearningRecord | None) -> bool:
    return record is not None and record.status == "learning"


def _activity_item(topic: Topic, record: LearningRecord) -> DashboardActivityItem:
    return DashboardActivityItem(
        topic_id=topic.id,
        title=topic.title,
        category=topic.category,
        status=record.status,
        progress_percent=record.progress_percent,
        mastery_level=record.mastery_level,
        review_count=record.review_count,
        last_studied_at=record.last_studied_at,
    )


def _review_reason(record: LearningRecord) -> str:
    if record.status == "learning":
        return "学习中的知识点需要再次复习"
    return "继续复习以提升掌握程度"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def _published_tags(problem: Problem) -> list[Topic]:
    return [
        tag.topic
        for tag in problem.problem_tags
        if tag.topic is not None and tag.topic.status == "published"
    ]


def _get_accumulator(
    weak_by_topic: dict[UUID, WeakTopicAccumulator],
    topic: Topic,
) -> WeakTopicAccumulator:
    if topic.id not in weak_by_topic:
        weak_by_topic[topic.id] = WeakTopicAccumulator(topic=topic)
    return weak_by_topic[topic.id]


def _weakness_score(item: WeakTopicAccumulator) -> int:
    return min(
        100,
        item.learning_score
        + item.open_mistake_count * 15
        + item.failed_submission_count * 20
        + item.stale_learning_bonus,
    )


def _weak_reason(item: WeakTopicAccumulator) -> str:
    parts: list[str] = []
    if item.learning_score:
        parts.append("掌握度偏低")
    if item.stale_learning_bonus:
        parts.append("学习记录已超过 7 天未更新")
    if item.open_mistake_count:
        parts.append(f"有 {item.open_mistake_count} 条未解决复盘")
    if item.failed_submission_count:
        parts.append(f"近期有 {item.failed_submission_count} 次失败提交")
    return "；".join(parts) or "已有学习信号提示需要关注"


def _weak_action(item: WeakTopicAccumulator) -> str:
    if item.open_mistake_count:
        return "先处理关联复盘笔记，再回到知识点巩固。"
    if item.failed_submission_count:
        return "复盘失败提交并重做相关题目。"
    if item.learning_score:
        return "重新学习知识点并补充练习。"
    return "继续跟进该知识点。"


def _build_weak_topics(
    *,
    rows: list[tuple[Topic, LearningRecord | None]],
    open_mistakes: list[MistakeNote],
    failed_submissions: list[Submission],
) -> tuple[list[DashboardWeakTopic], dict[UUID, WeakTopicAccumulator]]:
    weak_by_topic: dict[UUID, WeakTopicAccumulator] = {}
    stale_before = _now_utc() - timedelta(days=STALE_LEARNING_DAYS)

    for topic, record in rows:
        if record is None or record.status == "mastered":
            continue
        accumulator = _get_accumulator(weak_by_topic, topic)
        if record.mastery_level < 3:
            accumulator.learning_score = max(accumulator.learning_score, (5 - record.mastery_level) * 10)
            accumulator.signals.add("掌握度较低")
        if record.status == "learning" and _as_aware(record.last_studied_at) < stale_before:
            accumulator.stale_learning_bonus = 10
            accumulator.signals.add("超过 7 天未学习")

    for note in open_mistakes:
        topics: list[Topic] = []
        if note.topic is not None and note.topic.status == "published":
            topics.append(note.topic)
        if note.problem is not None:
            topics.extend(_published_tags(note.problem))
        for topic in {topic.id: topic for topic in topics}.values():
            accumulator = _get_accumulator(weak_by_topic, topic)
            accumulator.open_mistake_count += 1
            accumulator.signals.add("有未解决复盘")

    for submission in failed_submissions:
        if submission.verdict not in FAILED_VERDICTS or submission.problem is None:
            continue
        for topic in _published_tags(submission.problem):
            accumulator = _get_accumulator(weak_by_topic, topic)
            accumulator.failed_submission_count += 1
            accumulator.signals.add("近期提交失败")

    sorted_items = sorted(
        weak_by_topic.values(),
        key=lambda item: (-_weakness_score(item), item.topic.category, item.topic.order_index, item.topic.title),
    )
    weak_topics = [
        DashboardWeakTopic(
            topic_id=item.topic.id,
            title=item.topic.title,
            category=item.topic.category,
            weakness_score=_weakness_score(item),
            signals=sorted(item.signals),
            reason=_weak_reason(item),
            recommended_action=_weak_action(item),
        )
        for item in sorted_items
        if _weakness_score(item) > 0
    ][:5]
    return weak_topics, weak_by_topic


def _action(
    *,
    action_type: str,
    title: str,
    reason: str,
    priority: int,
    target_type: str,
    target_id: UUID,
) -> DashboardRecommendationAction:
    return DashboardRecommendationAction(
        type=action_type,
        title=title,
        reason=reason,
        priority=priority,
        target_type=target_type,
        target_id=target_id,
    )


def _latest_attempt_by_node(attempts: list[LadderExamAttempt]) -> dict[UUID, LadderExamAttempt]:
    latest: dict[UUID, LadderExamAttempt] = {}
    for attempt in attempts:
        if attempt.node_id not in latest:
            latest[attempt.node_id] = attempt
    return latest


def _current_ladder_node(
    nodes: list[LearningPathNode],
    progress_by_node: dict[UUID, NodeUserProgress],
) -> LearningPathNode | None:
    status_by_node = {node.id: _node_status(node, nodes, progress_by_node) for node in nodes}
    current = next(
        (
            node
            for node in nodes
            if status_by_node[node.id] != "locked"
            and not bool(progress_by_node.get(node.id) and progress_by_node[node.id].material_completed)
        ),
        None,
    )
    if current is None:
        current = next(
            (
                node
                for node in nodes
                if status_by_node[node.id] != "locked"
                and not bool(progress_by_node.get(node.id) and progress_by_node[node.id].exam_passed)
            ),
            None,
        )
    if current is None and nodes:
        return nodes[0]
    return current


def _ladder_next_action(
    *,
    node: LearningPathNode,
    status_value: str,
    progress: NodeUserProgress | None,
    latest_attempt: LadderExamAttempt | None,
) -> str | None:
    if status_value == "locked":
        return "通过前置节点考试后继续推进。"
    if progress is None or not progress.material_completed:
        return f"阅读「{node.title}」资料并标记完成。"
    if not progress.practice_completed:
        return f"完成「{node.title}」节点练习。"
    if not progress.exam_passed:
        if latest_attempt is not None and latest_attempt.status == "submitted" and not latest_attempt.passed:
            return f"复盘「{node.title}」考试结果后重新生成考试。"
        return f"参加「{node.title}」节点考试。"
    return "当前节点已通过，继续推进后续节点。"


def _build_ladder_progress(
    *,
    path: LearningPath | None,
    progress_by_node: dict[UUID, NodeUserProgress],
    latest_attempts: dict[UUID, LadderExamAttempt],
) -> DashboardLadderProgress | None:
    if path is None:
        return None
    nodes = sorted(path.nodes, key=lambda node: node.node_index)
    if not nodes:
        return DashboardLadderProgress(
            path_id=path.id,
            template_name=path.template.name if path.template is not None else "学习天梯",
            goal_track=path.goal_track,
            current_level=path.current_level,
            total_nodes=0,
            material_completed_nodes=0,
            practice_completed_nodes=0,
            exam_passed_nodes=0,
            current_node_id=None,
            current_node_title=None,
            current_node_status=None,
            next_action=None,
        )

    current = _current_ladder_node(nodes, progress_by_node)
    current_status = _node_status(current, nodes, progress_by_node) if current is not None else None
    current_progress = progress_by_node.get(current.id) if current is not None else None
    current_attempt = latest_attempts.get(current.id) if current is not None else None

    return DashboardLadderProgress(
        path_id=path.id,
        template_name=path.template.name if path.template is not None else "学习天梯",
        goal_track=path.goal_track,
        current_level=path.current_level,
        total_nodes=len(nodes),
        material_completed_nodes=sum(1 for progress in progress_by_node.values() if progress.material_completed),
        practice_completed_nodes=sum(1 for progress in progress_by_node.values() if progress.practice_completed),
        exam_passed_nodes=sum(1 for progress in progress_by_node.values() if progress.exam_passed),
        current_node_id=current.id if current is not None else None,
        current_node_title=current.title if current is not None else None,
        current_node_status=current_status,
        next_action=_ladder_next_action(
            node=current,
            status_value=current_status,
            progress=current_progress,
            latest_attempt=current_attempt,
        )
        if current is not None and current_status is not None
        else None,
    )


def _build_ladder_actions(
    *,
    ladder_progress: DashboardLadderProgress | None,
    latest_attempts: dict[UUID, LadderExamAttempt],
) -> list[DashboardRecommendationAction]:
    if ladder_progress is None or ladder_progress.current_node_id is None:
        return []
    status_value = ladder_progress.current_node_status
    if status_value == "locked" or status_value == "passed":
        return []

    current_node_id = ladder_progress.current_node_id
    latest_attempt = latest_attempts.get(current_node_id)
    if status_value == "unlocked":
        return [
            _action(
                action_type="read_ladder_material",
                title=f"阅读天梯资料：{ladder_progress.current_node_title}",
                reason="当前天梯节点已解锁，先完成资料阅读才能继续练习和考试。",
                priority=1,
                target_type="ladder_node",
                target_id=current_node_id,
            )
        ]
    if status_value == "material_done":
        return [
            _action(
                action_type="complete_ladder_practice",
                title=f"完成节点练习：{ladder_progress.current_node_title}",
                reason="资料已经读完，完成节点练习后才能生成考试。",
                priority=1,
                target_type="ladder_node",
                target_id=current_node_id,
            )
        ]
    if status_value == "practice_done":
        if latest_attempt is not None and latest_attempt.status == "submitted" and not latest_attempt.passed:
            return [
                _action(
                    action_type="retry_ladder_exam",
                    title=f"重试节点考试：{ladder_progress.current_node_title}",
                    reason=f"最近一次考试得分 {latest_attempt.score if latest_attempt.score is not None else '未知'}，尚未达到通过线。",
                    priority=1,
                    target_type="ladder_node",
                    target_id=current_node_id,
                )
            ]
        return [
            _action(
                action_type="take_ladder_exam",
                title=f"参加节点考试：{ladder_progress.current_node_title}",
                reason="节点练习已完成，通过考试后将解锁下一阶段。",
                priority=1,
                target_type="ladder_node",
                target_id=current_node_id,
            )
        ]
    return []


def _build_recommendation_actions(
    *,
    weak_topics: list[DashboardWeakTopic],
    open_mistakes: list[MistakeNote],
    failed_submissions: list[Submission],
    ladder_actions: list[DashboardRecommendationAction],
) -> list[DashboardRecommendationAction]:
    actions: list[DashboardRecommendationAction] = []
    actions.extend(ladder_actions[:2])

    for note in open_mistakes[:5]:
        actions.append(
            _action(
                action_type="review_mistake",
                title=f"复盘：{note.title}",
                reason="这条复盘仍未解决，优先处理能直接减少薄弱点。",
                priority=1,
                target_type="mistake",
                target_id=note.id,
            )
        )
        if len(actions) >= 5:
            return actions

    recommended_problem_ids: set[UUID] = set()
    for submission in failed_submissions[:5]:
        if submission.problem_id is None:
            continue
        if submission.problem_id in recommended_problem_ids:
            continue
        recommended_problem_ids.add(submission.problem_id)
        actions.append(
            _action(
                action_type="retry_problem",
                title=f"重做：P{submission.problem_display_id} {submission.problem_title}",
                reason=f"最近一次提交结果为 {submission.verdict}，建议复盘后重新提交。",
                priority=2,
                target_type="problem",
                target_id=submission.problem_id,
            )
        )
        if len(actions) >= 5:
            return actions

    for weak_topic in weak_topics:
        actions.append(
            _action(
                action_type="review_topic",
                title=f"复习：{weak_topic.title}",
                reason=weak_topic.reason,
                priority=2,
                target_type="topic",
                target_id=weak_topic.topic_id,
            )
        )
        if len(actions) >= 5:
            return actions

    return actions


def _topic_tag_schema(topic: Topic) -> DashboardPracticeTopicTag:
    return DashboardPracticeTopicTag(
        id=topic.id,
        title=topic.title,
        slug=topic.slug,
        category=topic.category,
    )


def _build_practice_recommendations(
    *,
    weak_by_topic: dict[UUID, WeakTopicAccumulator],
    problems: list[Problem],
    accepted_problem_ids: set[UUID],
) -> list[DashboardPracticeRecommendation]:
    if not weak_by_topic:
        return []

    weak_topic_ids = set(weak_by_topic)
    weak_categories = {item.topic.category for item in weak_by_topic.values()}
    recommendations: list[tuple[int, Problem, str]] = []
    seen: set[UUID] = set()

    for problem in problems:
        tags = _published_tags(problem)
        tag_ids = {topic.id for topic in tags}
        category_match = any(topic.category in weak_categories for topic in tags)
        accepted_penalty = 50 if problem.id in accepted_problem_ids else 0
        if tag_ids & weak_topic_ids:
            priority_score = 0 + accepted_penalty
            reason = "关联到当前薄弱知识点，适合用于针对性练习。"
        elif category_match:
            priority_score = 20 + accepted_penalty
            reason = "与薄弱知识点属于同一分类，可作为补充练习。"
        else:
            continue
        recommendations.append((priority_score, problem, reason))

    result: list[DashboardPracticeRecommendation] = []
    for rank, (_, problem, reason) in enumerate(
        sorted(recommendations, key=lambda item: (item[0], item[1].display_id, item[1].created_at))[:5],
        start=1,
    ):
        if problem.id in seen:
            continue
        seen.add(problem.id)
        result.append(
            DashboardPracticeRecommendation(
                problem_id=problem.id,
                display_id=problem.display_id,
                title=problem.title,
                difficulty=problem.difficulty,
                topic_tags=[_topic_tag_schema(topic) for topic in _published_tags(problem)],
                reason=reason,
                priority=min(3, rank),
            )
        )
    return result


def get_summary(db: Session, *, user_id: UUID) -> DashboardSummary:
    rows = get_dashboard_topic_rows(db, user_id=user_id)
    total = len(rows)
    learning = sum(1 for _, record in rows if _is_learning(record))
    mastered = sum(1 for _, record in rows if _is_mastered(record))
    started = sum(1 for _, record in rows if _is_started(record))
    not_started = total - started
    total_estimated_minutes = sum(topic.estimated_minutes for topic, _ in rows)
    completed_estimated_minutes = sum(topic.estimated_minutes for topic, record in rows if _is_mastered(record))

    status_counts = [
        DashboardStatusCount(status="not_started", label="未开始", count=not_started, percent=_percent(not_started, total)),
        DashboardStatusCount(status="learning", label="学习中", count=learning, percent=_percent(learning, total)),
        DashboardStatusCount(status="mastered", label="已掌握", count=mastered, percent=_percent(mastered, total)),
    ]

    category_progress: list[DashboardCategoryProgress] = []
    categories = sorted({topic.category for topic, _ in rows})
    for category in categories:
        category_rows = [(topic, record) for topic, record in rows if topic.category == category]
        category_total = len(category_rows)
        category_started = sum(1 for _, record in category_rows if _is_started(record))
        category_mastered = sum(1 for _, record in category_rows if _is_mastered(record))
        category_estimated = sum(topic.estimated_minutes for topic, _ in category_rows)
        category_completed = sum(
            topic.estimated_minutes for topic, record in category_rows if _is_mastered(record)
        )
        category_progress.append(
            DashboardCategoryProgress(
                category=category,
                total_topics=category_total,
                started_topics=category_started,
                mastered_topics=category_mastered,
                progress_percent=_percent(category_mastered, category_total),
                estimated_minutes=category_estimated,
                completed_estimated_minutes=category_completed,
            )
        )

    records = [(topic, record) for topic, record in rows if record is not None]
    recent_activity = [
        _activity_item(topic, record)
        for topic, record in sorted(records, key=lambda item: item[1].last_studied_at, reverse=True)[:5]
    ]

    review_candidates = [
        (topic, record)
        for topic, record in records
        if record.status != "mastered" and record.status != "not_started" and record.mastery_level < 5
    ]
    review_candidates.sort(
        key=lambda item: (
            0 if item[1].status == "learning" else 1,
            item[1].next_review_at is None,
            item[1].next_review_at,
            item[1].mastery_level,
            item[1].last_studied_at,
        )
    )
    review_queue = [
        DashboardReviewItem(
            **_activity_item(topic, record).model_dump(),
            next_review_at=record.next_review_at,
            reason=_review_reason(record),
        )
        for topic, record in review_candidates[:5]
    ]

    unstarted_topics = [topic for topic, record in rows if record is None]
    unstarted_topics.sort(key=lambda topic: (topic.order_index, topic.difficulty_score, topic.created_at))
    if unstarted_topics:
        next_steps = [
            DashboardNextStep(
                topic_id=topic.id,
                title=topic.title,
                category=topic.category,
                level=topic.level,
                difficulty_score=topic.difficulty_score,
                estimated_minutes=topic.estimated_minutes,
                reason="下一个尚未开始的已发布知识点",
                rank=index,
            )
            for index, topic in enumerate(unstarted_topics[:3], start=1)
        ]
    else:
        non_mastered = [(topic, record) for topic, record in records if record.status != "mastered"]
        non_mastered.sort(key=lambda item: (item[1].mastery_level, item[1].last_studied_at))
        next_steps = [
            DashboardNextStep(
                topic_id=topic.id,
                title=topic.title,
                category=topic.category,
                level=topic.level,
                difficulty_score=topic.difficulty_score,
                estimated_minutes=topic.estimated_minutes,
                reason="继续推进尚未掌握的知识点",
                rank=index,
            )
            for index, (topic, record) in enumerate(non_mastered[:3], start=1)
        ]

    path = get_dashboard_active_ladder_path(db, user_id=user_id)
    progress_by_node = get_progress_for_path(db, path=path, user_id=user_id) if path is not None else {}
    latest_ladder_attempts = _latest_attempt_by_node(
        get_dashboard_latest_ladder_attempts(
            db,
            user_id=user_id,
            node_ids=[node.id for node in path.nodes] if path is not None else [],
        )
    )
    ladder_progress = _build_ladder_progress(
        path=path,
        progress_by_node=progress_by_node,
        latest_attempts=latest_ladder_attempts,
    )
    ladder_actions = _build_ladder_actions(
        ladder_progress=ladder_progress,
        latest_attempts=latest_ladder_attempts,
    )

    open_mistakes = get_dashboard_open_mistakes(db, user_id=user_id)
    failed_submissions = get_dashboard_failed_submissions(db, user_id=user_id)
    weak_topics, weak_by_topic = _build_weak_topics(
        rows=rows,
        open_mistakes=open_mistakes,
        failed_submissions=failed_submissions,
    )
    recommendation_actions = _build_recommendation_actions(
        weak_topics=weak_topics,
        open_mistakes=open_mistakes,
        failed_submissions=failed_submissions,
        ladder_actions=ladder_actions,
    )
    practice_recommendations = _build_practice_recommendations(
        weak_by_topic=weak_by_topic,
        problems=get_dashboard_user_problems(db, user_id=user_id),
        accepted_problem_ids=get_dashboard_accepted_problem_ids(db, user_id=user_id),
    )

    return DashboardSummary(
        total_topics=total,
        started_topics=started,
        mastered_topics=mastered,
        learning_topics=learning,
        progress_percent=_percent(mastered, total),
        not_started_topics=not_started,
        total_estimated_minutes=total_estimated_minutes,
        completed_estimated_minutes=completed_estimated_minutes,
        status_counts=status_counts,
        category_progress=category_progress,
        recent_activity=recent_activity,
        review_queue=review_queue,
        next_steps=next_steps,
        weak_topics=weak_topics,
        recommendation_actions=recommendation_actions,
        practice_recommendations=practice_recommendations,
        ladder_progress=ladder_progress,
    )
