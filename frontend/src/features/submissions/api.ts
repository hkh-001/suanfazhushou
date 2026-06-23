import { apiFetch } from "@/lib/api/client";

import type {
  SubmissionDiagnosisResponse,
  SubmissionLanguage,
  SubmissionResponse
} from "./types";

export function createSubmission(payload: {
  problem_id: string;
  language: SubmissionLanguage;
  source_code: string;
}): Promise<SubmissionResponse> {
  return apiFetch<SubmissionResponse>("/submissions", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchSubmission(id: string): Promise<SubmissionResponse> {
  return apiFetch<SubmissionResponse>(`/submissions/${id}`);
}

export function diagnoseSubmission(id: string): Promise<SubmissionDiagnosisResponse> {
  return apiFetch<SubmissionDiagnosisResponse>(`/submissions/${id}/ai-diagnose`, {
    method: "POST",
    timeoutMs: 65000
  });
}
