"use client";

import { useCallback, useEffect, useState } from "react";

import { isAuthRequiredError } from "@/features/auth/hooks";
import { ApiError } from "@/lib/api/client";

import { createSavedCodeReview, deleteCodeReview, fetchCodeReview, fetchCodeReviews } from "./api";
import type { CodeReviewDetail, CodeReviewPayload, PaginatedCodeReviews } from "./types";

export function getCodeReviewErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后继续使用。";
  }
  if (error instanceof ApiError) {
    if (error.code === "CODE_REVIEW_NOT_FOUND") {
      return "诊断记录不存在，或你没有访问权限。";
    }
    if (error.code === "PROBLEM_NOT_FOUND") {
      return "关联题目不存在，或你没有访问权限。";
    }
    if (error.code === "TOPIC_NOT_FOUND") {
      return "关联知识点不存在或当前不可见。";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

export function useCodeReviews(page: number) {
  const [data, setData] = useState<PaginatedCodeReviews | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchCodeReviews(page)
      .then(setData)
      .catch((err: unknown) => setError(getCodeReviewErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [page]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useCodeReview(id: string) {
  const [data, setData] = useState<CodeReviewDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    if (!id) {
      setData(null);
      setError(null);
      setLoading(false);
      return Promise.resolve();
    }
    setLoading(true);
    setError(null);
    return fetchCodeReview(id)
      .then((response) => setData(response.data))
      .catch((err: unknown) => setError(getCodeReviewErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useCreateCodeReview() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (payload: CodeReviewPayload) => {
    setLoading(true);
    setError(null);
    try {
      return await createSavedCodeReview(payload);
    } catch (err) {
      setError(getCodeReviewErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, error };
}

export function useDeleteCodeReview(id: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      return await deleteCodeReview(id);
    } catch (err) {
      setError(getCodeReviewErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [id]);

  return { submit, loading, error };
}
