import { apiFetch } from "@/lib/api/client";

import type { PaginatedProblems, ProblemDeleteResponse, ProblemPayload, ProblemResponse, ProblemUpdatePayload } from "./types";

export function fetchProblems(page = 1, pageSize = 20): Promise<PaginatedProblems> {
  return apiFetch<PaginatedProblems>(`/problems?page=${page}&page_size=${pageSize}`);
}

export function fetchProblem(id: string): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>(`/problems/${id}`);
}

export function createProblem(payload: ProblemPayload): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>("/problems", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProblem(id: string, payload: ProblemUpdatePayload): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>(`/problems/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteProblem(id: string): Promise<ProblemDeleteResponse> {
  return apiFetch<ProblemDeleteResponse>(`/problems/${id}`, {
    method: "DELETE"
  });
}
