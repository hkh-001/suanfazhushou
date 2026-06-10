"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import { isAuthRequiredError } from "@/features/auth/hooks";
import { fetchDashboardSummary } from "./api";
import type { DashboardSummary } from "./types";

function getErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后继续使用。";
  }
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "未知错误，请稍后重试。";
}

export function useDashboardSummary() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchDashboardSummary()
      .then((result) => {
        setData(result.data);
      })
      .catch((err: unknown) => {
        setError(getErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}
