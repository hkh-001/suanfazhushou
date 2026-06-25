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
