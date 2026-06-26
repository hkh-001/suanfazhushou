from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_topics: int
    started_topics: int
    mastered_topics: int
    learning_topics: int
    progress_percent: int
    not_started_topics: int
    total_estimated_minutes: int
    completed_estimated_minutes: int
    status_counts: list["DashboardStatusCount"]
    category_progress: list["DashboardCategoryProgress"]
    recent_activity: list["DashboardActivityItem"]
    review_queue: list["DashboardReviewItem"]
    next_steps: list["DashboardNextStep"]
    weak_topics: list["DashboardWeakTopic"]
    recommendation_actions: list["DashboardRecommendationAction"]
    practice_recommendations: list["DashboardPracticeRecommendation"]
    ladder_progress: "DashboardLadderProgress | None" = None


class DashboardStatusCount(BaseModel):
    status: str
    label: str
    count: int
    percent: int


class DashboardCategoryProgress(BaseModel):
    category: str
    total_topics: int
    started_topics: int
    mastered_topics: int
    progress_percent: int
    estimated_minutes: int
    completed_estimated_minutes: int


class DashboardActivityItem(BaseModel):
    topic_id: UUID
    title: str
    category: str
    status: str
    progress_percent: int
    mastery_level: int
    review_count: int
    last_studied_at: datetime


class DashboardReviewItem(DashboardActivityItem):
    next_review_at: datetime | None = None
    reason: str


class DashboardNextStep(BaseModel):
    topic_id: UUID
    title: str
    category: str
    level: str
    difficulty_score: int
    estimated_minutes: int
    reason: str
    rank: int


class DashboardWeakTopic(BaseModel):
    topic_id: UUID
    title: str
    category: str
    weakness_score: int
    signals: list[str]
    reason: str
    recommended_action: str


class DashboardRecommendationAction(BaseModel):
    type: Literal[
        "review_topic",
        "review_mistake",
        "retry_problem",
        "practice_problem",
        "read_ladder_material",
        "complete_ladder_practice",
        "take_ladder_exam",
        "retry_ladder_exam",
    ]
    title: str
    reason: str
    priority: int
    target_type: Literal["topic", "mistake", "problem", "submission", "ladder_node"]
    target_id: UUID


class DashboardLadderProgress(BaseModel):
    path_id: UUID
    template_name: str
    goal_track: str
    current_level: str
    total_nodes: int
    material_completed_nodes: int
    practice_completed_nodes: int
    exam_passed_nodes: int
    current_node_id: UUID | None
    current_node_title: str | None
    current_node_status: Literal["locked", "unlocked", "material_done", "practice_done", "passed"] | None
    next_action: str | None


class DashboardPracticeTopicTag(BaseModel):
    id: UUID
    title: str
    slug: str
    category: str


class DashboardPracticeRecommendation(BaseModel):
    problem_id: UUID
    display_id: int
    title: str
    difficulty: str
    topic_tags: list[DashboardPracticeTopicTag]
    reason: str
    priority: int
