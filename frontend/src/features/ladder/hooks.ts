"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";

import { completeLadderNodeMaterial, fetchLadder, fetchLadderNode, submitLadderNodePractice } from "./api";
import type { LadderNodeDetail, LadderPracticeSubmitPayload, LadderSummary } from "./types";

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
    if (error.code === "NODE_LOCKED") {
      return "该节点尚未解锁，请先完成前置节点资料。";
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
