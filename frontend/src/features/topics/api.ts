import { apiFetch } from "@/lib/api/client";
import type { InteractiveLessonResponse, LearningRecordPayload, PaginatedTopics, TopicResponse } from "./types";

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

export function createInteractiveLesson(topicId: string): Promise<InteractiveLessonResponse> {
  return apiFetch<InteractiveLessonResponse>(`/topics/${topicId}/interactive-lessons`, {
    method: "POST",
    timeoutMs: 30000
  });
}

export function fetchInteractiveLesson(lessonId: string): Promise<InteractiveLessonResponse> {
  return apiFetch<InteractiveLessonResponse>(`/interactive-lessons/${lessonId}`);
}

export function refreshInteractiveLesson(lessonId: string): Promise<InteractiveLessonResponse> {
  return apiFetch<InteractiveLessonResponse>(`/interactive-lessons/${lessonId}/refresh`, {
    method: "POST",
    timeoutMs: 30000
  });
}
