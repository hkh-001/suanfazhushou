import { apiFetch } from "@/lib/api/client";

import type {
  MistakeNoteDeleteResponse,
  MistakeNotePayload,
  MistakeNoteResponse,
  MistakeNoteUpdatePayload,
  PaginatedMistakeNotes,
  ReviewStatus
} from "./types";

export function fetchMistakeNotes(page = 1, pageSize = 20, status?: ReviewStatus | "all", init?: RequestInit): Promise<PaginatedMistakeNotes> {
  const query = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (status && status !== "all") {
    query.set("status", status);
  }
  return apiFetch<PaginatedMistakeNotes>(`/mistakes?${query.toString()}`, init);
}

export function fetchMistakeNote(id: string, init?: RequestInit): Promise<MistakeNoteResponse> {
  return apiFetch<MistakeNoteResponse>(`/mistakes/${id}`, init);
}

export function createMistakeNote(payload: MistakeNotePayload): Promise<MistakeNoteResponse> {
  return apiFetch<MistakeNoteResponse>("/mistakes", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateMistakeNote(id: string, payload: MistakeNoteUpdatePayload): Promise<MistakeNoteResponse> {
  return apiFetch<MistakeNoteResponse>(`/mistakes/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function deleteMistakeNote(id: string): Promise<MistakeNoteDeleteResponse> {
  return apiFetch<MistakeNoteDeleteResponse>(`/mistakes/${id}`, {
    method: "DELETE"
  });
}
