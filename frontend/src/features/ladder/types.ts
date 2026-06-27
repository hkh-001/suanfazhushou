export type LadderNodeStatus = "locked" | "unlocked" | "material_done" | "practice_done" | "passed";

export type LadderPathSummary = {
  id: string;
  status: string;
  goal_track: string;
  current_level: string;
  template_name: string;
  created_at: string;
};

export type LadderNodeSummary = {
  id: string;
  topic_id: string | null;
  phase_index: number;
  node_index: number;
  algorithm_key: string;
  title: string;
  summary: string;
  status: LadderNodeStatus;
  locked: boolean;
  material_completed: boolean;
  practice_completed: boolean;
  exam_passed: boolean;
};

export type LadderPhase = {
  phase_index: number;
  title: string;
  description: string | null;
  nodes: LadderNodeSummary[];
};

export type LadderSummary = {
  path: LadderPathSummary;
  phases: LadderPhase[];
  current_node_id: string | null;
};

export type LadderResourceLink = {
  title: string;
  url: string;
  source: string | null;
};

export type LadderNodeDetail = LadderNodeSummary & {
  path_id: string;
  material_markdown: string;
  resource_links: LadderResourceLink[];
  practice_items: LadderPracticeItem[];
  practice_completed_at: string | null;
};

export type LadderChoiceOption = {
  id: string;
  text: string;
};

export type LadderChoicePracticeItem = {
  id: string;
  type: "choice";
  prompt: string;
  options: LadderChoiceOption[];
};

export type LadderCodingPracticeItem = {
  id: string;
  type: "coding";
  prompt: string;
  self_check: string;
};

export type LadderPracticeItem = LadderChoicePracticeItem | LadderCodingPracticeItem;

export type LadderPracticeSubmitPayload = {
  choice_answers: Array<{ item_id: string; option_id: string }>;
  completed_coding_item_ids: string[];
};

export type LadderChoiceResult = {
  item_id: string;
  correct: boolean;
  explanation: string | null;
};

export type LadderPracticeSubmitResult = {
  score: number;
  passed: boolean;
  practice_completed: boolean;
  choice_results: LadderChoiceResult[];
  ladder: LadderSummary;
};

export type LadderExamQuestionType = "single_choice" | "code_reading";
export type LadderExamAttemptStatus = "generated" | "submitted";

export type LadderExamOption = {
  id: string;
  text: string;
};

export type LadderExamQuestion = {
  id: string;
  type: LadderExamQuestionType;
  prompt: string;
  options: LadderExamOption[];
  explanation: string | null;
  correct_option_id: string | null;
};

export type LadderExamAnswer = {
  question_id: string;
  option_id: string;
};

export type LadderExamQuestionResult = {
  question_id: string;
  selected_option_id: string | null;
  correct_option_id: string;
  correct: boolean;
  points: number;
  explanation: string;
};

export type LadderExamAttempt = {
  id: string;
  node_id: string;
  status: LadderExamAttemptStatus;
  questions: LadderExamQuestion[];
  score: number | null;
  passed: boolean;
  submitted_answers: LadderExamAnswer[] | null;
  results: LadderExamQuestionResult[] | null;
  created_at: string;
  submitted_at: string | null;
};

export type LadderExamGenerationResult = {
  attempt: LadderExamAttempt;
};

export type LadderExamSubmitPayload = {
  answers: LadderExamAnswer[];
};

export type LadderExamSubmitResult = {
  attempt: LadderExamAttempt;
  score: number;
  passed: boolean;
  ladder: LadderSummary;
};

export type InteractiveLessonStatus = "pending" | "submitted" | "processing" | "completed" | "failed";

export type LadderInteractiveLesson = {
  id: string;
  source_type: "topic" | "ladder_node";
  topic_id: string | null;
  node_id: string | null;
  provider: "openmaic";
  status: InteractiveLessonStatus;
  title: string;
  classroom_url: string | null;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
};

export type LadderInteractiveLessonResponse = {
  data: LadderInteractiveLesson;
};
