"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";

import { getCurrentUser, logout } from "./api";
import type { AuthUser } from "./types";

const authRequiredCodes = new Set(["AUTH_REQUIRED", "INVALID_SESSION", "TOKEN_EXPIRED", "TOKEN_INVALID"]);

export function isAuthRequiredError(error: unknown): boolean {
  return error instanceof ApiError && authRequiredCodes.has(error.code);
}

function getErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后继续使用。";
  }
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

export function useCurrentUser() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    return getCurrentUser()
      .then((response) => {
        setUser(response.data);
      })
      .catch((err: unknown) => {
        setUser(null);
        setError(getErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const signOut = useCallback(() => {
    setLoading(true);
    setError(null);
    return logout()
      .then(() => reload())
      .catch((err: unknown) => {
        setError(getErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [reload]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { user, loading, error, reload, signOut };
}
