from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.learning_record import LearningRecord
from app.models.mistake_note import MistakeNote
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.topic import Topic
from app.repositories.dashboard import (
    get_dashboard_accepted_problem_ids,
    get_dashboard_failed_submissions,
    get_dashboard_open_mistakes,
    get_dashboard_topic_rows,
    get_dashboard_user_problems,
)
from app.schemas.dashboard import (
    DashboardActivityItem,
    DashboardCategoryProgress,
    DashboardNextStep,
    DashboardPracticeRecommendation,
    DashboardPracticeTopicTag,
    DashboardRecommendationAction,
    DashboardReviewItem,
    DashboardStatusCount,
    DashboardSummary,
    DashboardWeakTopic,
)


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
        return "Learning topic needs another review"
    return "Continue reviewing to reach mastery"


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


def _build_recommendation_actions(
    *,
    weak_topics: list[DashboardWeakTopic],
    open_mistakes: list[MistakeNote],
    failed_submissions: list[Submission],
) -> list[DashboardRecommendationAction]:
    actions: list[DashboardRecommendationAction] = []
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
        DashboardStatusCount(
            status="not_started",
            label="Not started",
            count=not_started,
            percent=_percent(not_started, total),
        ),
        DashboardStatusCount(
            status="learning",
            label="Learning",
            count=learning,
            percent=_percent(learning, total),
        ),
        DashboardStatusCount(
            status="mastered",
            label="Mastered",
            count=mastered,
            percent=_percent(mastered, total),
        ),
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
                reason="Next published topic with no learning record",
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
                reason="Continue a topic that is not mastered yet",
                rank=index,
            )
            for index, (topic, record) in enumerate(non_mastered[:3], start=1)
        ]

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
    )
