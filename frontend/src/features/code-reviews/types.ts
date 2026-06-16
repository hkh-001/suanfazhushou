export type CodeReviewLanguage = "cpp" | "python";

export type RefTopic = {
  id: string;
  title: string;
  slug: string;
  category: string;
};

export type RefProblem = {
  id: string;
  display_id: number;
  title: string;
};

export type CodeReviewListItem = {
  id: string;
  topic_id: string | null;
  problem_id: string | null;
  language: CodeReviewLanguage;
  question: string | null;
  analysis_result: string;
  model: string | null;
  prompt_type: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  topic: RefTopic | null;
  problem: RefProblem | null;
  created_at: string;
  updated_at: string;
};

export type CodeReviewDetail = CodeReviewListItem & {
  code: string;
};

export type CodeReviewPayload = {
  topic_id?: string | null;
  problem_id?: string | null;
  language: CodeReviewLanguage;
  question?: string | null;
  code: string;
  analysis_result: string;
  model?: string | null;
  prompt_type?: string | null;
  input_tokens?: number | null;
  output_tokens?: number | null;
};

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PaginatedCodeReviews = {
  data: CodeReviewListItem[];
  pagination: Pagination;
};

export type CodeReviewResponse = {
  data: CodeReviewDetail;
};

export type CodeReviewDeleteResponse = {
  data: {
    success: boolean;
  };
};
