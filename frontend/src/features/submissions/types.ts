export type SubmissionLanguage = "cpp" | "python";
export type SubmissionVerdict =
  | "accepted"
  | "wrong_answer"
  | "compile_error"
  | "runtime_error"
  | "time_limit_exceeded"
  | "memory_limit_exceeded"
  | "output_limit_exceeded"
  | "internal_error";

export type SubmissionCaseResult = {
  case_index: number;
  name: string | null;
  is_sample: boolean;
  verdict: string;
  execution_time_ms: number | null;
  memory_kb: number | null;
  input_text: string | null;
  expected_output_text: string | null;
  actual_output: string | null;
  error_message: string | null;
};

export type SubmissionDetail = {
  id: string;
  problem: {
    id: string | null;
    display_id: number;
    title: string;
  };
  language: SubmissionLanguage;
  source_code: string;
  verdict: SubmissionVerdict;
  passed_case_count: number;
  total_case_count: number;
  execution_time_ms: number | null;
  memory_kb: number | null;
  compile_output: string | null;
  error_message: string | null;
  case_results: SubmissionCaseResult[];
  created_at: string;
  finished_at: string;
};

export type SubmissionResponse = {
  data: SubmissionDetail;
};
