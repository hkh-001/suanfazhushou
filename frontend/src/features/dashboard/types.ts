export type DashboardStatus = "not_started" | "learning" | "mastered";

export type DashboardStatusCount = {
  status: DashboardStatus;
  label: string;
  count: number;
  percent: number;
};

export type DashboardCategoryProgress = {
  category: string;
  total_topics: number;
  started_topics: number;
  mastered_topics: number;
  progress_percent: number;
  estimated_minutes: number;
  completed_estimated_minutes: number;
};

export type DashboardActivityItem = {
  topic_id: string;
  title: string;
  category: string;
  status: DashboardStatus;
  progress_percent: number;
  mastery_level: number;
  review_count: number;
  last_studied_at: string;
};

export type DashboardReviewItem = DashboardActivityItem & {
  next_review_at: string | null;
  reason: string;
};

export type DashboardNextStep = {
  topic_id: string;
  title: string;
  category: string;
  level: string;
  difficulty_score: number;
  estimated_minutes: number;
  reason: string;
  rank: number;
};

export type DashboardWeakTopic = {
  topic_id: string;
  title: string;
  category: string;
  weakness_score: number;
  signals: string[];
  reason: string;
  recommended_action: string;
};

export type DashboardRecommendationAction = {
  type:
    | "review_topic"
    | "review_mistake"
    | "retry_problem"
    | "practice_problem"
    | "read_ladder_material"
    | "complete_ladder_practice"
    | "take_ladder_exam"
    | "retry_ladder_exam";
  title: string;
  reason: string;
  priority: number;
  target_type: "topic" | "mistake" | "problem" | "submission" | "ladder_node";
  target_id: string;
};

export type DashboardLadderProgress = {
  path_id: string;
  template_name: string;
  goal_track: string;
  current_level: string;
  total_nodes: number;
  material_completed_nodes: number;
  practice_completed_nodes: number;
  exam_passed_nodes: number;
  current_node_id: string | null;
  current_node_title: string | null;
  current_node_status: "locked" | "unlocked" | "material_done" | "practice_done" | "passed" | null;
  next_action: string | null;
};

export type DashboardPracticeTopicTag = {
  id: string;
  title: string;
  slug: string;
  category: string;
};

export type DashboardPracticeRecommendation = {
  problem_id: string;
  display_id: number;
  title: string;
  difficulty: string;
  topic_tags: DashboardPracticeTopicTag[];
  reason: string;
  priority: number;
};

export type DashboardSummary = {
  total_topics: number;
  started_topics: number;
  learning_topics: number;
  mastered_topics: number;
  progress_percent: number;
  not_started_topics: number;
  total_estimated_minutes: number;
  completed_estimated_minutes: number;
  status_counts: DashboardStatusCount[];
  category_progress: DashboardCategoryProgress[];
  recent_activity: DashboardActivityItem[];
  review_queue: DashboardReviewItem[];
  next_steps: DashboardNextStep[];
  weak_topics: DashboardWeakTopic[];
  recommendation_actions: DashboardRecommendationAction[];
  practice_recommendations: DashboardPracticeRecommendation[];
  ladder_progress: DashboardLadderProgress | null;
};

export type DashboardResponse = {
  data: DashboardSummary;
};
