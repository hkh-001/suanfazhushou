"use client";

import { useCallback, useEffect, useState } from "react";

import { isAuthRequiredError } from "@/features/auth/hooks";
import { ApiError } from "@/lib/api/client";

import {
  createProblem,
  deleteProblem,
  fetchProblem,
  fetchProblems,
  fetchPublicProblem,
  fetchPublicProblems,
  importProblemZip,
  updateProblem
} from "./api";
import type { PaginatedProblems, ProblemDetail, ProblemPayload, ProblemUpdatePayload } from "./types";

export function getProblemErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后继续使用。";
  }
  if (error instanceof ApiError) {
    if (error.code === "PROBLEM_SLUG_ALREADY_EXISTS") {
      return "当前题目标识已存在，请换一个 slug。";
    }
    if (error.code === "TOPIC_NOT_FOUND") {
      return "关联的知识点不存在或当前不可见。";
    }
    if (error.code === "PROBLEM_NOT_FOUND") {
      return "题目不存在，或你没有访问权限。";
    }
    if (error.code === "PUBLIC_PROBLEM_FORBIDDEN") {
      return "只有 admin 可以创建或修改公共题目。";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

export function useProblems(page: number, pageSize = 20) {
  const [data, setData] = useState<PaginatedProblems | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    return fetchProblems(page, pageSize, { signal })
      .then((result) => {
        if (!signal?.aborted) {
          setData(result);
        }
      })
      .catch((err: unknown) => {
        if (!signal?.aborted) {
          setError(getProblemErrorMessage(err));
        }
      })
      .finally(() => {
        if (!signal?.aborted) {
          setLoading(false);
        }
      });
  }, [page, pageSize]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function usePublicProblems(page: number, pageSize = 20) {
  const [data, setData] = useState<PaginatedProblems | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback((signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    return fetchPublicProblems(page, pageSize, { signal })
      .then((result) => {
        if (!signal?.aborted) {
          setData(result);
        }
      })
      .catch((err: unknown) => {
        if (!signal?.aborted) {
          setError(getProblemErrorMessage(err));
        }
      })
      .finally(() => {
        if (!signal?.aborted) {
          setLoading(false);
        }
      });
  }, [page, pageSize]);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useProblem(id: string, visibility: "private" | "public" = "private") {
  const [data, setData] = useState<ProblemDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    const request = visibility === "public" ? fetchPublicProblem(id) : fetchProblem(id);
    return request
      .then((result) => {
        setData(result.data);
      })
      .catch((err: unknown) => {
        setError(getProblemErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id, visibility]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useCreateProblem() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (payload: ProblemPayload) => {
    setLoading(true);
    setError(null);
    try {
      return await createProblem(payload);
    } catch (err) {
      setError(getProblemErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, error };
}

export function useImportProblemZip() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    try {
      return await importProblemZip(file);
    } catch (err) {
      setError(getProblemErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, error };
}

export function useUpdateProblem(id: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const submit = useCallback(
    async (payload: ProblemUpdatePayload) => {
      setLoading(true);
      setError(null);
      setSuccess(false);
      try {
        const result = await updateProblem(id, payload);
        setSuccess(true);
        return result;
      } catch (err) {
        setError(getProblemErrorMessage(err));
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [id]
  );

  return { submit, loading, error, success };
}

export function useDeleteProblem(id: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      return await deleteProblem(id);
    } catch (err) {
      setError(getProblemErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [id]);

  return { submit, loading, error };
}
