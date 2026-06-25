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
};
