export type LearningStatus = {
  status: "not_started" | "learning" | "mastered";
  progress_percent: number;
  mastery_level: number;
  review_count: number;
  last_studied_at: string | null;
  next_review_at: string | null;
  note: string | null;
};

export type TopicListItem = {
  id: string;
  title: string;
  slug: string;
  category: string;
  level: string;
  difficulty_score: number;
  summary: string;
  estimated_minutes: number;
  order_index: number;
  learning_status: LearningStatus;
};

export type TopicDetail = TopicListItem & {
  content_markdown: string;
  template_code_cpp: string | null;
  template_code_python: string | null;
  complexity_note: string | null;
  common_pitfalls: string | null;
  published_at: string | null;
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PaginatedTopics = {
  data: TopicListItem[];
  pagination: Pagination;
};

export type TopicResponse = {
  data: TopicDetail;
};

export type LearningRecordPayload = {
  topic_id: string;
  status: "not_started" | "learning" | "mastered";
  progress_percent: number;
  mastery_level: number;
  note?: string | null;
};
