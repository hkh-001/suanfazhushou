export type ProblemDifficulty = "beginner" | "basic" | "intermediate" | "advanced";

export type ProblemTopicTag = {
  id: string;
  title: string;
  slug: string;
  category: string;
};

export type ProblemListItem = {
  id: string;
  title: string;
  slug: string;
  source: string | null;
  source_url: string | null;
  difficulty: ProblemDifficulty;
  estimated_minutes: number | null;
  is_ai_generated: boolean;
  is_published: boolean;
  created_by_user_id: string;
  topic_tags: ProblemTopicTag[];
  created_at: string;
  updated_at: string;
};

export type ProblemDetail = ProblemListItem & {
  description_markdown: string;
  input_format: string | null;
  output_format: string | null;
  constraints: string | null;
  sample_input: string | null;
  sample_output: string | null;
  hint: string | null;
  solution_markdown: string | null;
  solution_code_cpp: string | null;
  solution_code_python: string | null;
  published_at: string | null;
};

export type ProblemPayload = {
  title: string;
  slug?: string | null;
  source?: string | null;
  source_url?: string | null;
  difficulty: ProblemDifficulty;
  estimated_minutes?: number | null;
  description_markdown: string;
  input_format?: string | null;
  output_format?: string | null;
  constraints?: string | null;
  sample_input?: string | null;
  sample_output?: string | null;
  hint?: string | null;
  solution_markdown?: string | null;
  solution_code_cpp?: string | null;
  solution_code_python?: string | null;
  topic_ids?: string[];
};

export type ProblemUpdatePayload = Partial<ProblemPayload> & {
  topic_ids?: string[];
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PaginatedProblems = {
  data: ProblemListItem[];
  pagination: Pagination;
};

export type ProblemResponse = {
  data: ProblemDetail;
};

export type ProblemDeleteResponse = {
  data: {
    success: boolean;
  };
};
