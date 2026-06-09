export type AIUsage = {
  input_tokens: number | null;
  output_tokens: number | null;
};

export type AIResponseData = {
  result: string;
  prompt_type: string;
  model: string;
  usage: AIUsage;
};

export type AIResponse = {
  data: AIResponseData;
};

export type ChatPayload = {
  topic_id?: string | null;
  question: string;
  mode: "beginner" | "advanced";
};

export type CodeReviewPayload = {
  topic_id?: string | null;
  language: "cpp" | "python";
  code: string;
  question?: string | null;
};

export type ProblemGenerationPayload = {
  topic_id?: string | null;
  difficulty: "beginner" | "basic" | "intermediate";
  requirements?: string | null;
};
