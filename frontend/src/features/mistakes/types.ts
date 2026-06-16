import type { RefProblem, RefTopic } from "@/features/code-reviews/types";

export type ReviewStatus = "open" | "reviewing" | "resolved";

export type MistakeCodeReviewRef = {
  id: string;
  language: string;
  question: string | null;
  created_at: string;
};

export type MistakeNoteListItem = {
  id: string;
  problem_id: string | null;
  topic_id: string | null;
  code_review_id: string | null;
  title: string;
  error_type: string | null;
  root_cause: string;
  review_status: ReviewStatus;
  resolved_at: string | null;
  problem: RefProblem | null;
  topic: RefTopic | null;
  code_review: MistakeCodeReviewRef | null;
  created_at: string;
  updated_at: string;
};

export type MistakeNoteDetail = MistakeNoteListItem & {
  wrong_code: string | null;
  fixed_code: string | null;
  fix_suggestion: string | null;
  ai_summary: string | null;
  user_reflection: string | null;
};

export type MistakeNotePayload = {
  problem_id?: string | null;
  topic_id?: string | null;
  code_review_id?: string | null;
  title: string;
  error_type?: string | null;
  root_cause: string;
  wrong_code?: string | null;
  fixed_code?: string | null;
  fix_suggestion?: string | null;
  ai_summary?: string | null;
  user_reflection?: string | null;
  review_status: ReviewStatus;
};

export type MistakeNoteUpdatePayload = Partial<MistakeNotePayload>;

export type Pagination = {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
};

export type PaginatedMistakeNotes = {
  data: MistakeNoteListItem[];
  pagination: Pagination;
};

export type MistakeNoteResponse = {
  data: MistakeNoteDetail;
};

export type MistakeNoteDeleteResponse = {
  data: {
    success: boolean;
  };
};
