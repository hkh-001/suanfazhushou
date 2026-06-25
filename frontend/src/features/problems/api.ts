import { apiFetch } from "@/lib/api/client";

import type {
  GeneratedProblemSavePayload,
  PaginatedProblems,
  ProblemDeleteResponse,
  ProblemImportResponse,
  ProblemPayload,
  ProblemResponse,
  ProblemUpdatePayload
} from "./types";

export function fetchProblems(page = 1, pageSize = 20, init?: RequestInit): Promise<PaginatedProblems> {
  return apiFetch<PaginatedProblems>(`/problems?page=${page}&page_size=${pageSize}`, init);
}

export function fetchPublicProblems(page = 1, pageSize = 20, init?: RequestInit): Promise<PaginatedProblems> {
  return apiFetch<PaginatedProblems>(`/problems/public?page=${page}&page_size=${pageSize}`, init);
}

export function fetchProblem(id: string): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>(`/problems/${id}`);
}

export function fetchPublicProblem(id: string): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>(`/problems/public/${id}`);
}

export function createProblem(payload: ProblemPayload): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>("/problems", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function saveGeneratedProblem(payload: GeneratedProblemSavePayload): Promise<ProblemResponse> {
  return apiFetch<ProblemResponse>("/problems/save-ai-generated", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function importProblemZip(file: File): Promise<ProblemImportResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<ProblemImportResponse>("/problems/import/zip", {
    method: "POST",
    body: formData
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
