import { apiFetch } from "@/lib/api/client";

import type { DashboardResponse } from "./types";

export function fetchDashboardSummary(): Promise<DashboardResponse> {
  return apiFetch<DashboardResponse>("/dashboard/summary");
}
