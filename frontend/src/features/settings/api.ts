import { apiFetch } from "@/lib/api/client";

import type { AISettingsPayload, AISettingsResponse, AISettingsTestResponse } from "./types";

export function fetchAISettings(): Promise<AISettingsResponse> {
  return apiFetch<AISettingsResponse>("/settings/ai");
}

export function saveAISettings(payload: AISettingsPayload): Promise<AISettingsResponse> {
  return apiFetch<AISettingsResponse>("/settings/ai", {
    method: "PUT",
    body: JSON.stringify(payload)
  });
}

export function clearAISettings(): Promise<AISettingsResponse> {
  return apiFetch<AISettingsResponse>("/settings/ai", {
    method: "DELETE"
  });
}

export function testAISettings(): Promise<AISettingsTestResponse> {
  return apiFetch<AISettingsTestResponse>("/settings/ai/test", {
    method: "POST"
  });
}
