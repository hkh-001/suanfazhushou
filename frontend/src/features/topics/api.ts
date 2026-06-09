import { apiFetch } from "@/lib/api/client";
import type { LearningRecordPayload, PaginatedTopics, TopicResponse } from "./types";

export function fetchTopics(page = 1, pageSize = 20): Promise<PaginatedTopics> {
  return apiFetch<PaginatedTopics>(`/topics?page=${page}&page_size=${pageSize}`);
}

export function fetchTopic(id: string): Promise<TopicResponse> {
  return apiFetch<TopicResponse>(`/topics/${id}`);
}

export function updateLearningRecord(payload: LearningRecordPayload) {
  return apiFetch("/learning/records", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
