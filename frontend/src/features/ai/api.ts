import { apiFetch } from "@/lib/api/client";

import type { AIResponse, ChatPayload, CodeReviewPayload, ProblemGenerationPayload } from "./types";

const AI_REQUEST_TIMEOUT_MS = 65000;
const PROBLEM_GENERATION_TIMEOUT_MS = 240000;

export function submitChat(payload: ChatPayload): Promise<AIResponse> {
  return apiFetch<AIResponse>("/ai/chat", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: AI_REQUEST_TIMEOUT_MS
  });
}

export function submitCodeReview(payload: CodeReviewPayload): Promise<AIResponse> {
  return apiFetch<AIResponse>("/ai/code-review", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: AI_REQUEST_TIMEOUT_MS
  });
}

export function submitProblemGeneration(payload: ProblemGenerationPayload): Promise<AIResponse> {
  return apiFetch<AIResponse>("/ai/generate-problem", {
    method: "POST",
    body: JSON.stringify(payload),
    timeoutMs: PROBLEM_GENERATION_TIMEOUT_MS
  });
}
