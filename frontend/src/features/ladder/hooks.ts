"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";

import {
  completeLadderNodeMaterial,
  createLadderNodeInteractiveLesson,
  fetchLadder,
  fetchLadderNode,
  generateLadderExam,
  refreshLadderInteractiveLesson,
  submitLadderExam,
  submitLadderNodePractice
} from "./api";
import type {
  LadderExamGenerationResult,
  LadderExamSubmitPayload,
  LadderInteractiveLesson,
  LadderNodeDetail,
  LadderPracticeSubmitPayload,
  LadderSummary
} from "./types";

function userMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (
      error.code === "AUTH_REQUIRED" ||
      error.code === "INVALID_SESSION" ||
      error.code === "TOKEN_EXPIRED" ||
      error.code === "TOKEN_INVALID"
    ) {
      return "请先登录后继续使用。";
    }
    if (error.code === "LADDER_TEMPLATE_NOT_FOUND") {
      return "暂未找到适合当前画像的学习天梯模板。";
    }
    if (error.code === "LADDER_NODE_NOT_FOUND") {
      return "学习天梯节点不存在。";
    }
    if (error.code === "NODE_LOCKED") {
      return "该节点尚未解锁，请先通过前置节点考试。";
    }
    if (error.code === "NODE_MATERIAL_REQUIRED") {
      return "先完成资料阅读后再开始练习。";
    }
    if (error.code === "LADDER_PRACTICE_NOT_FOUND") {
      return "当前节点暂未配置练习。";
    }
    if (error.code === "LADDER_PRACTICE_VALIDATION_ERROR") {
      return "练习提交内容有误，请检查选项。";
    }
    if (error.code === "LADDER_EXAM_REQUIRE_MATERIAL") {
      return "先完成资料阅读后再参加考试。";
    }
    if (error.code === "LADDER_EXAM_REQUIRE_PRACTICE") {
      return "先通过节点练习后再参加考试。";
    }
    if (error.code === "LADDER_EXAM_ALREADY_PASSED") {
      return "该节点考试已经通过。";
    }
    if (error.code === "LADDER_EXAM_GENERATION_FAILED") {
      return "AI 生成考试失败，请重新生成。";
    }
    if (error.code === "LADDER_EXAM_VALIDATION_ERROR") {
      return "考试提交内容有误，请检查答案。";
    }
    if (error.code === "AI_CONFIG_MISSING") {
      return "AI 服务尚未配置，无法生成考试。";
    }
    if (error.code === "AI_PROVIDER_TIMEOUT") {
      return "AI 服务请求超时，请稍后重试。";
    }
    if (error.code === "AI_PROVIDER_ERROR") {
      return "AI 服务暂时不可用，请稍后重试。";
    }
    if (error.code === "PROMPT_TEMPLATE_NOT_FOUND") {
      return "考试生成模板尚未初始化，请先运行 prompt seed。";
    }
    if (
      error.code === "FEATURE_DISABLED" ||
      error.code === "OPENMAIC_CONFIG_MISSING" ||
      error.code === "OPENMAIC_TIMEOUT" ||
      error.code === "OPENMAIC_UNAVAILABLE" ||
      error.code === "OPENMAIC_INVALID_RESPONSE" ||
      error.code === "OPENMAIC_JOB_NOT_FOUND"
    ) {
      return "互动课堂服务暂未启用或暂不可用，请稍后再试。";
    }
    return error.message;
  }
  return "学习天梯加载失败，请稍后重试。";
}

export function useLadder() {
  const [data, setData] = useState<LadderSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchLadder());
    } catch (err) {
      setError(userMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load, setData };
}

export function useLadderNode(nodeId: string | null) {
  const [data, setData] = useState<LadderNodeDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!nodeId) {
      setData(null);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setData(await fetchLadderNode(nodeId));
    } catch (err) {
      setError(userMessage(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [nodeId]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load, setData };
}

export function useCompleteLadderMaterial() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const complete = useCallback(async (nodeId: string) => {
    setLoading(true);
    setError(null);
    try {
      return await completeLadderNodeMaterial(nodeId);
    } catch (err) {
      const message = userMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { complete, loading, error };
}

export function useSubmitLadderPractice() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (nodeId: string, payload: LadderPracticeSubmitPayload) => {
    setLoading(true);
    setError(null);
    try {
      return await submitLadderNodePractice(nodeId, payload);
    } catch (err) {
      const message = userMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, error };
}

export function useGenerateLadderExam() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async (nodeId: string): Promise<LadderExamGenerationResult> => {
    setLoading(true);
    setError(null);
    try {
      return await generateLadderExam(nodeId);
    } catch (err) {
      const message = userMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { generate, loading, error };
}

export function useSubmitLadderExam() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async (attemptId: string, payload: LadderExamSubmitPayload) => {
    setLoading(true);
    setError(null);
    try {
      return await submitLadderExam(attemptId, payload);
    } catch (err) {
      const message = userMessage(err);
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  return { submit, loading, error };
}

export function useLadderInteractiveLesson() {
  const [lesson, setLesson] = useState<LadderInteractiveLesson | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generate = useCallback(async (nodeId: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await createLadderNodeInteractiveLesson(nodeId);
      setLesson(result.data);
      return result.data;
    } catch (err) {
      setError(userMessage(err));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async (lessonId: string) => {
    setError(null);
    try {
      const result = await refreshLadderInteractiveLesson(lessonId);
      setLesson(result.data);
      return result.data;
    } catch (err) {
      setError(userMessage(err));
      return null;
    }
  }, []);

  return { lesson, loading, error, generate, refresh, setLesson };
}
