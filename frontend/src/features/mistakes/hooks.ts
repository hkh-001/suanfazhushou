"use client";

import { useCallback, useEffect, useState } from "react";

import { isAuthRequiredError } from "@/features/auth/hooks";
import { ApiError } from "@/lib/api/client";

import { createMistakeNote, deleteMistakeNote, fetchMistakeNote, fetchMistakeNotes, updateMistakeNote } from "./api";
import type { MistakeNoteDetail, MistakeNotePayload, MistakeNoteUpdatePayload, PaginatedMistakeNotes, ReviewStatus } from "./types";

export function getMistakeErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后继续使用。";
  }
  if (error instanceof ApiError) {
    if (error.code === "MISTAKE_NOTE_NOT_FOUND") {
      return "复盘笔记不存在，或你没有访问权限。";
    }
    if (error.code === "CODE_REVIEW_NOT_FOUND") {
      return "关联诊断记录不存在，或你没有访问权限。";
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

export function useMistakeNotes(page: number, status: ReviewStatus | "all") {
  const [data, setData] = useState<PaginatedMistakeNotes | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchMistakeNotes(page, 20, status)
      .then(setData)
      .catch((err: unknown) => setError(getMistakeErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [page, status]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useMistakeNote(id: string) {
  const [data, setData] = useState<MistakeNoteDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchMistakeNote(id)
      .then((response) => setData(response.data))
      .catch((err: unknown) => setError(getMistakeErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useCreateMistakeNote() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (payload: MistakeNotePayload) => {
    setLoading(true);
    setError(null);
    try {
      return await createMistakeNote(payload);
    } catch (err) {
      setError(getMistakeErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, error };
}

export function useUpdateMistakeNote(id: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const submit = useCallback(
    async (payload: MistakeNoteUpdatePayload) => {
      setLoading(true);
      setError(null);
      setSuccess(false);
      try {
        const response = await updateMistakeNote(id, payload);
        setSuccess(true);
        return response;
      } catch (err) {
        setError(getMistakeErrorMessage(err));
        throw err;
      } finally {
        setLoading(false);
      }
    },
    [id]
  );

  return { submit, loading, error, success };
}

export function useDeleteMistakeNote(id: string) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      return await deleteMistakeNote(id);
    } catch (err) {
      setError(getMistakeErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [id]);

  return { submit, loading, error };
}
