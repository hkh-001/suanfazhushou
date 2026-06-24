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
  type: "review_topic" | "review_mistake" | "retry_problem" | "practice_problem";
  title: string;
  reason: string;
  priority: number;
  target_type: "topic" | "mistake" | "problem" | "submission";
  target_id: string;
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
};

export type DashboardResponse = {
  data: DashboardSummary;
};
