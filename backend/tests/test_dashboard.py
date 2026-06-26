from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select

from app.models.ladder import LadderTemplate, LearningPath, LearningPathNode, NodeUserProgress
from app.models.ladder_exam import LadderExamAttempt
from app.models.learning_record import LearningRecord
from app.models.mistake_note import MistakeNote
from app.models.problem import Problem, ProblemTag
from app.models.submission import Submission
from app.models.topic import Topic
from app.models.user import User


def create_topic(
    db_session,
    *,
    title: str,
    category: str = "Dashboard Test",
    order_index: int = 1,
    difficulty_score: int = 3,
    estimated_minutes: int = 20,
) -> Topic:
    topic = Topic(
        title=title,
        slug=f"{title.lower().replace(' ', '-')}-{uuid4().hex}",
        category=category,
        level="beginner",
        difficulty_score=difficulty_score,
        summary=f"{title} summary",
        content_markdown=f"{title} content",
        estimated_minutes=estimated_minutes,
        status="published",
        published_at=datetime.now(timezone.utc),
        order_index=order_index,
    )
    db_session.add(topic)
    db_session.commit()
    return topic


def create_record(
    db_session,
    *,
    user: User,
    topic: Topic,
    status: str,
    progress_percent: int,
    mastery_level: int,
    last_studied_at: datetime,
    review_count: int = 0,
) -> LearningRecord:
    record = LearningRecord(
        user_id=user.id,
        topic_id=topic.id,
        status=status,
        progress_percent=progress_percent,
        mastery_level=mastery_level,
        review_count=review_count,
        last_studied_at=last_studied_at,
    )
    db_session.add(record)
    db_session.commit()
    return record


def ensure_record(
    db_session,
    *,
    user: User,
    topic: Topic,
    status: str,
    progress_percent: int,
    mastery_level: int,
    last_studied_at: datetime,
) -> LearningRecord:
    record = db_session.scalar(
        select(LearningRecord).where(
            LearningRecord.user_id == user.id,
            LearningRecord.topic_id == topic.id,
        )
    )
    if record is None:
        return create_record(
            db_session,
            user=user,
            topic=topic,
            status=status,
            progress_percent=progress_percent,
            mastery_level=mastery_level,
            last_studied_at=last_studied_at,
        )

    record.status = status
    record.progress_percent = progress_percent
    record.mastery_level = mastery_level
    record.last_studied_at = last_studied_at
    db_session.commit()
    return record


def create_problem_with_topic(
    db_session,
    *,
    user: User,
    topic: Topic,
    title: str = "Dashboard Practice Problem",
    display_id: int = 9001,
) -> Problem:
    problem = Problem(
        display_id=display_id,
        title=title,
        slug=f"{title.lower().replace(' ', '-')}-{uuid4().hex}",
        difficulty="basic",
        estimated_minutes=20,
        description_markdown="Practice problem",
        created_by_user_id=user.id,
    )
    db_session.add(problem)
    db_session.flush()
    db_session.add(ProblemTag(problem_id=problem.id, topic_id=topic.id))
    db_session.commit()
    db_session.refresh(problem)
    return problem


def create_mistake(
    db_session,
    *,
    user: User,
    topic: Topic,
    status: str = "open",
    title: str = "Dashboard Mistake",
) -> MistakeNote:
    note = MistakeNote(
        user_id=user.id,
        topic_id=topic.id,
        title=title,
        root_cause="Boundary condition was missed.",
        review_status=status,
    )
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)
    return note


def create_submission(
    db_session,
    *,
    user: User,
    problem: Problem | None,
    verdict: str,
) -> Submission:
    submission = Submission(
        user_id=user.id,
        problem_id=problem.id if problem else None,
        problem_title=problem.title if problem else "Deleted Problem",
        problem_display_id=problem.display_id if problem else 9999,
        language="python",
        source_code="print(0)",
        verdict=verdict,
        passed_case_count=0 if verdict != "accepted" else 1,
        total_case_count=1,
        execution_time_ms=10,
        memory_kb=1024,
        finished_at=datetime.now(timezone.utc),
    )
    db_session.add(submission)
    db_session.commit()
    db_session.refresh(submission)
    return submission


def create_ladder_path_for_dashboard(db_session, *, user: User) -> tuple[LearningPath, LearningPathNode]:
    template = LadderTemplate(
        goal_track="self_study",
        current_level="beginner",
        name="Dashboard Ladder Path",
        description="Dashboard ladder progress",
        template_data={"phases": []},
        version=1,
        is_default=False,
    )
    db_session.add(template)
    db_session.flush()
    path = LearningPath(
        user_id=user.id,
        template_id=template.id,
        goal_track="self_study",
        current_level="beginner",
        status="active",
    )
    db_session.add(path)
    db_session.flush()
    first_node = LearningPathNode(
        path_id=path.id,
        phase_index=1,
        node_index=1,
        algorithm_key="complexity",
        title="时间复杂度",
        summary="学习复杂度估算。",
        material_markdown="# 时间复杂度",
        resource_links=[],
        practice_items=[],
        unlock_rule={},
    )
    second_node = LearningPathNode(
        path_id=path.id,
        phase_index=1,
        node_index=2,
        algorithm_key="binary-search",
        title="二分查找",
        summary="学习边界收缩。",
        material_markdown="# 二分查找",
        resource_links=[],
        practice_items=[],
        unlock_rule={},
    )
    db_session.add_all([first_node, second_node])
    db_session.flush()
    db_session.add(
        NodeUserProgress(
            user_id=user.id,
            node_id=first_node.id,
            material_completed=True,
            practice_completed=True,
            exam_passed=False,
        )
    )
    db_session.add(NodeUserProgress(user_id=user.id, node_id=second_node.id))
    db_session.commit()
    return path, first_node


def test_dashboard_summary_empty_learning_records_recommends_unstarted_topics(
    client,
    db_session,
    dev_user,
) -> None:
    topic = create_topic(db_session, title="Dashboard Empty Topic", order_index=-100)

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total_topics"] >= 1
    assert body["not_started_topics"] >= 1
    assert body["recent_activity"] == []
    assert body["review_queue"] == []
    assert body["next_steps"][0]["topic_id"] == str(topic.id)
    assert body["next_steps"][0]["rank"] == 1
    assert body["next_steps"][0]["reason"] == "下一个尚未开始的已发布知识点"
    assert body["ladder_progress"] is None


def test_dashboard_summary_returns_ladder_progress_and_exam_action(client, db_session, dev_user) -> None:
    _, first_node = create_ladder_path_for_dashboard(db_session, user=dev_user)

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    ladder = body["ladder_progress"]
    assert ladder["template_name"] == "Dashboard Ladder Path"
    assert ladder["total_nodes"] == 2
    assert ladder["material_completed_nodes"] == 1
    assert ladder["practice_completed_nodes"] == 1
    assert ladder["exam_passed_nodes"] == 0
    assert ladder["current_node_id"] == str(first_node.id)
    assert ladder["current_node_status"] == "practice_done"
    assert "考试" in ladder["next_action"]
    action = next(item for item in body["recommendation_actions"] if item["target_type"] == "ladder_node")
    assert action["type"] == "take_ladder_exam"
    assert action["target_id"] == str(first_node.id)


def test_dashboard_summary_recommends_retry_for_failed_ladder_exam(client, db_session, dev_user) -> None:
    path, first_node = create_ladder_path_for_dashboard(db_session, user=dev_user)
    db_session.add(
        LadderExamAttempt(
            user_id=dev_user.id,
            path_id=path.id,
            node_id=first_node.id,
            status="submitted",
            exam_payload={"questions": []},
            submitted_answers={"answers": []},
            result_payload={"results": []},
            score=72,
            passed=False,
        )
    )
    db_session.commit()

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    action = next(item for item in body["recommendation_actions"] if item["target_type"] == "ladder_node")
    assert action["type"] == "retry_ladder_exam"
    assert "72" in action["reason"]


def test_dashboard_summary_returns_mixed_progress_and_category_progress(
    client,
    db_session,
    dev_user,
) -> None:
    now = datetime.now(timezone.utc)
    learning_topic = create_topic(
        db_session,
        title="Dashboard Learning Topic",
        category="Dashboard Arrays",
        estimated_minutes=30,
    )
    mastered_topic = create_topic(
        db_session,
        title="Dashboard Mastered Topic",
        category="Dashboard Arrays",
        estimated_minutes=40,
    )
    create_topic(
        db_session,
        title="Dashboard Unstarted Topic",
        category="Dashboard Strings",
        estimated_minutes=50,
    )
    create_record(
        db_session,
        user=dev_user,
        topic=learning_topic,
        status="learning",
        progress_percent=50,
        mastery_level=2,
        last_studied_at=now - timedelta(hours=2),
    )
    create_record(
        db_session,
        user=dev_user,
        topic=mastered_topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now - timedelta(hours=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["learning_topics"] >= 1
    assert body["mastered_topics"] >= 1
    assert body["started_topics"] >= 2
    assert body["total_estimated_minutes"] >= 120
    assert body["completed_estimated_minutes"] >= 40

    arrays = next(item for item in body["category_progress"] if item["category"] == "Dashboard Arrays")
    assert arrays["total_topics"] == 2
    assert arrays["started_topics"] == 2
    assert arrays["mastered_topics"] == 1
    assert arrays["progress_percent"] == 50
    assert arrays["estimated_minutes"] == 70
    assert arrays["completed_estimated_minutes"] == 40

    statuses = {item["status"]: item for item in body["status_counts"]}
    assert set(statuses) == {"not_started", "learning", "mastered"}
    assert statuses["learning"]["count"] >= 1
    assert statuses["mastered"]["count"] >= 1


def test_dashboard_recent_activity_is_sorted_and_limited(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topics = [
        create_topic(db_session, title=f"Dashboard Recent {index}", category="Dashboard Recent", order_index=index)
        for index in range(6)
    ]
    for index, topic in enumerate(topics):
        create_record(
            db_session,
            user=dev_user,
            topic=topic,
            status="learning",
            progress_percent=50,
            mastery_level=2,
            last_studied_at=now + timedelta(minutes=index),
        )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    recent = response.json()["data"]["recent_activity"]
    assert len(recent) == 5
    recent_titles = [item["title"] for item in recent]
    assert recent_titles[:5] == [
        "Dashboard Recent 5",
        "Dashboard Recent 4",
        "Dashboard Recent 3",
        "Dashboard Recent 2",
        "Dashboard Recent 1",
    ]


def test_dashboard_review_queue_rules(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    learning_topic = create_topic(db_session, title="Dashboard Review Learning")
    not_started_topic = create_topic(db_session, title="Dashboard Review Not Started")
    mastered_topic = create_topic(db_session, title="Dashboard Review Mastered")
    create_record(
        db_session,
        user=dev_user,
        topic=learning_topic,
        status="learning",
        progress_percent=50,
        mastery_level=2,
        last_studied_at=now - timedelta(days=2),
    )
    create_record(
        db_session,
        user=dev_user,
        topic=not_started_topic,
        status="not_started",
        progress_percent=0,
        mastery_level=0,
        last_studied_at=now - timedelta(days=3),
    )
    create_record(
        db_session,
        user=dev_user,
        topic=mastered_topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now - timedelta(days=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    review_queue = response.json()["data"]["review_queue"]
    review_ids = {item["topic_id"] for item in review_queue}
    assert str(learning_topic.id) in review_ids
    assert str(not_started_topic.id) not in review_ids
    assert str(mastered_topic.id) not in review_ids
    assert next(item for item in review_queue if item["topic_id"] == str(learning_topic.id))["reason"] == (
        "Learning topic needs another review"
    )


def test_dashboard_next_steps_fallbacks_to_non_mastered_when_all_topics_started(
    client,
    db_session,
    dev_user,
) -> None:
    now = datetime.now(timezone.utc)
    low_mastery_topic = create_topic(db_session, title="Dashboard Low Mastery", category="Dashboard Fallback")
    high_mastery_topic = create_topic(db_session, title="Dashboard High Mastery", category="Dashboard Fallback")
    for topic in db_session.scalars(select(Topic).where(Topic.status == "published")).all():
        ensure_record(
            db_session,
            user=dev_user,
            topic=topic,
            status="mastered",
            progress_percent=100,
            mastery_level=5,
            last_studied_at=now - timedelta(days=5),
        )
    ensure_record(
        db_session,
        user=dev_user,
        topic=low_mastery_topic,
        status="learning",
        progress_percent=40,
        mastery_level=1,
        last_studied_at=now,
    )
    ensure_record(
        db_session,
        user=dev_user,
        topic=high_mastery_topic,
        status="learning",
        progress_percent=80,
        mastery_level=4,
        last_studied_at=now - timedelta(hours=1),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    category_steps = [
        item for item in response.json()["data"]["next_steps"] if item["category"] == "Dashboard Fallback"
    ]
    assert category_steps[0]["topic_id"] == str(low_mastery_topic.id)
    assert category_steps[0]["rank"] == 1
    assert category_steps[0]["reason"] == "Continue a topic that is not mastered yet"


def test_dashboard_next_steps_empty_when_all_topics_mastered(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topic = create_topic(db_session, title="Dashboard All Mastered", category="Dashboard Complete")
    for published_topic in db_session.scalars(select(Topic).where(Topic.status == "published")).all():
        ensure_record(
            db_session,
            user=dev_user,
            topic=published_topic,
            status="mastered",
            progress_percent=100,
            mastery_level=5,
            last_studied_at=now,
        )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    category_steps = [
        item for item in response.json()["data"]["next_steps"] if item["category"] == "Dashboard Complete"
    ]
    assert category_steps == []


def test_dashboard_ignores_other_users_records(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topic = create_topic(db_session, title="Dashboard Isolation", category="Dashboard Isolation", order_index=-50)
    other_user = User(
        id=uuid4(),
        email=f"other-{uuid4()}@algomentor.local",
        username=f"other_{uuid4().hex[:8]}",
        student_id=f"other_{uuid4().hex[:8]}",
        name="其他用户",
        current_level="beginner",
        goal_track="self_study",
        learning_stage="beginner",
        target_track="algorithm_basics",
    )
    db_session.add(other_user)
    db_session.commit()
    create_record(
        db_session,
        user=other_user,
        topic=topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert str(topic.id) not in {item["topic_id"] for item in body["recent_activity"]}
    assert body["next_steps"][0]["topic_id"] == str(topic.id)


def test_dashboard_phase12_fields_empty_without_weakness_signals(client, db_session, dev_user) -> None:
    now = datetime.now(timezone.utc)
    topic = create_topic(db_session, title="Dashboard No Weak Signal", category="Dashboard Phase12 Empty")
    create_record(
        db_session,
        user=dev_user,
        topic=topic,
        status="mastered",
        progress_percent=100,
        mastery_level=5,
        last_studied_at=now,
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert "weak_topics" in body
    assert "recommendation_actions" in body
    assert "practice_recommendations" in body
    assert not [item for item in body["weak_topics"] if item["category"] == "Dashboard Phase12 Empty"]


def test_dashboard_low_mastery_and_stale_learning_create_weak_topic(client, db_session, dev_user) -> None:
    topic = create_topic(db_session, title="Dashboard Weak Learning", category="Dashboard Phase12 Learning")
    create_record(
        db_session,
        user=dev_user,
        topic=topic,
        status="learning",
        progress_percent=30,
        mastery_level=1,
        last_studied_at=datetime.now(timezone.utc) - timedelta(days=8),
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    weak = next(item for item in response.json()["data"]["weak_topics"] if item["topic_id"] == str(topic.id))
    assert weak["weakness_score"] == 50
    assert "掌握度较低" in weak["signals"]
    assert "超过 7 天未学习" in weak["signals"]
    assert "掌握度偏低" in weak["reason"]


def test_dashboard_open_mistake_adds_weakness_and_action(client, db_session, dev_user) -> None:
    topic = create_topic(db_session, title="Dashboard Mistake Topic", category="Dashboard Phase12 Mistake")
    mistake = create_mistake(db_session, user=dev_user, topic=topic, title="数组边界复盘")

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    weak = next(item for item in body["weak_topics"] if item["topic_id"] == str(topic.id))
    assert weak["weakness_score"] == 15
    assert "有未解决复盘" in weak["signals"]
    action = next(item for item in body["recommendation_actions"] if item["target_id"] == str(mistake.id))
    assert action["type"] == "review_mistake"
    assert action["priority"] == 1
    assert action["target_type"] == "mistake"


def test_dashboard_resolved_mistake_is_not_high_priority_recommendation(client, db_session, dev_user) -> None:
    topic = create_topic(db_session, title="Dashboard Resolved Mistake", category="Dashboard Phase12 Resolved")
    mistake = create_mistake(
        db_session,
        user=dev_user,
        topic=topic,
        status="resolved",
        title="已解决复盘",
    )

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert str(topic.id) not in {item["topic_id"] for item in body["weak_topics"]}
    assert str(mistake.id) not in {item["target_id"] for item in body["recommendation_actions"]}


def test_dashboard_failed_submission_affects_weak_topic_and_practice(client, db_session, dev_user) -> None:
    topic = create_topic(db_session, title="Dashboard Failed Submission", category="Dashboard Phase12 Submit")
    problem = create_problem_with_topic(
        db_session,
        user=dev_user,
        topic=topic,
        title="Failed Practice",
        display_id=9101,
    )
    create_submission(db_session, user=dev_user, problem=problem, verdict="wrong_answer")

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    weak = next(item for item in body["weak_topics"] if item["topic_id"] == str(topic.id))
    assert weak["weakness_score"] == 20
    assert "近期提交失败" in weak["signals"]
    retry_action = next(item for item in body["recommendation_actions"] if item["target_id"] == str(problem.id))
    assert retry_action["type"] == "retry_problem"
    assert retry_action["target_type"] == "problem"
    practice = next(item for item in body["practice_recommendations"] if item["problem_id"] == str(problem.id))
    assert practice["display_id"] == 9101
    assert practice["topic_tags"][0]["id"] == str(topic.id)


def test_dashboard_accepted_and_deleted_problem_submissions_do_not_create_weak_topics(
    client,
    db_session,
    dev_user,
) -> None:
    accepted_topic = create_topic(
        db_session,
        title="Dashboard Accepted Submission",
        category="Dashboard Phase12 Accepted",
    )
    accepted_problem = create_problem_with_topic(
        db_session,
        user=dev_user,
        topic=accepted_topic,
        title="Accepted Practice",
        display_id=9201,
    )
    create_submission(db_session, user=dev_user, problem=accepted_problem, verdict="accepted")
    deleted_submission = create_submission(db_session, user=dev_user, problem=None, verdict="wrong_answer")

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    weak_ids = {item["topic_id"] for item in body["weak_topics"]}
    assert str(accepted_topic.id) not in weak_ids
    assert str(deleted_submission.id) not in {item["target_id"] for item in body["recommendation_actions"]}


def test_dashboard_phase12_recommendations_are_user_isolated(client, db_session, dev_user) -> None:
    topic = create_topic(db_session, title="Dashboard Other User Weak", category="Dashboard Phase12 Isolation")
    other_user = User(
        id=uuid4(),
        email=f"phase12-other-{uuid4()}@algomentor.local",
        username=f"phase12_other_{uuid4().hex[:8]}",
        student_id=f"phase12_other_{uuid4().hex[:8]}",
        name="其他用户",
        current_level="beginner",
        goal_track="self_study",
        learning_stage="beginner",
        target_track="algorithm_basics",
    )
    db_session.add(other_user)
    db_session.commit()
    other_problem = create_problem_with_topic(
        db_session,
        user=other_user,
        topic=topic,
        title="Other User Practice",
        display_id=9301,
    )
    create_mistake(db_session, user=other_user, topic=topic, title="Other mistake")
    create_submission(db_session, user=other_user, problem=other_problem, verdict="wrong_answer")

    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    body = response.json()["data"]
    assert str(topic.id) not in {item["topic_id"] for item in body["weak_topics"]}
    assert str(other_problem.id) not in {item["problem_id"] for item in body["practice_recommendations"]}
