import { apiFetch } from "@/lib/api/client";

import type { AIResponse, ChatPayload, CodeReviewPayload, ProblemGenerationPayload } from "./types";

export function submitChat(payload: ChatPayload): Promise<AIResponse> {
  return apiFetch<AIResponse>("/ai/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitCodeReview(payload: CodeReviewPayload): Promise<AIResponse> {
  return apiFetch<AIResponse>("/ai/code-review", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function submitProblemGeneration(payload: ProblemGenerationPayload): Promise<AIResponse> {
  return apiFetch<AIResponse>("/ai/generate-problem", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
