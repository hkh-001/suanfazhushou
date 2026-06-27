"use client";

import { useCallback, useEffect, useState } from "react";

import { isAuthRequiredError } from "@/features/auth/hooks";
import { ApiError } from "@/lib/api/client";

import {
  createInteractiveLesson,
  fetchInteractiveLesson,
  fetchTopic,
  fetchTopics,
  refreshInteractiveLesson,
  updateLearningRecord
} from "./api";
import type { InteractiveLesson, LearningRecordPayload, PaginatedTopics, TopicDetail } from "./types";

function getErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后继续使用。";
  }
  if (error instanceof ApiError) {
    if (
      ["FEATURE_DISABLED", "OPENMAIC_CONFIG_MISSING", "OPENMAIC_UNAVAILABLE", "OPENMAIC_TIMEOUT"].includes(
        error.code
      )
    ) {
      return "互动课堂服务暂未启用或暂不可用，请稍后再试。";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "未知错误，请稍后重试。";
}

export function useTopics() {
  const [data, setData] = useState<PaginatedTopics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchTopics()
      .then((result) => {
        if (active) {
          setData(result);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setError(getErrorMessage(err));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  return { data, loading, error };
}

export function useTopic(id: string) {
  const [data, setData] = useState<TopicDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    return fetchTopic(id)
      .then((result) => {
        setData(result.data);
        setError(null);
      })
      .catch((err: unknown) => {
        setError(getErrorMessage(err));
      })
      .finally(() => {
        setLoading(false);
      });
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useUpdateLearningRecord() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const update = useCallback(async (payload: LearningRecordPayload) => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    try {
      await updateLearningRecord(payload);
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  return { update, loading, error, success };
}

export function useInteractiveLesson() {
  const [lesson, setLesson] = useState<InteractiveLesson | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async (topicId: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await createInteractiveLesson(topicId);
      setLesson(result.data);
      return result.data;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async (lessonId: string) => {
    setError(null);
    try {
      const result = await refreshInteractiveLesson(lessonId);
      setLesson(result.data);
      return result.data;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    }
  }, []);

  const load = useCallback(async (lessonId: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchInteractiveLesson(lessonId);
      setLesson(result.data);
      return result.data;
    } catch (err) {
      setError(getErrorMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { lesson, loading, error, generate, refresh, load, setLesson };
}
