import { apiFetch } from "@/lib/api/client";

import type {
  CodeReviewDeleteResponse,
  CodeReviewPayload,
  CodeReviewResponse,
  PaginatedCodeReviews
} from "./types";

export function createSavedCodeReview(payload: CodeReviewPayload): Promise<CodeReviewResponse> {
  return apiFetch<CodeReviewResponse>("/code-reviews", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function fetchCodeReviews(page = 1, pageSize = 20, init?: RequestInit): Promise<PaginatedCodeReviews> {
  return apiFetch<PaginatedCodeReviews>(`/code-reviews?page=${page}&page_size=${pageSize}`, init);
}

export function fetchCodeReview(id: string, init?: RequestInit): Promise<CodeReviewResponse> {
  return apiFetch<CodeReviewResponse>(`/code-reviews/${id}`, init);
}

export function deleteCodeReview(id: string): Promise<CodeReviewDeleteResponse> {
  return apiFetch<CodeReviewDeleteResponse>(`/code-reviews/${id}`, {
    method: "DELETE"
  });
}
