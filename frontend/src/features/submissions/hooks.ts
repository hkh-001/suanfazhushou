"use client";

import { useCallback, useEffect, useState } from "react";

import { isAuthRequiredError } from "@/features/auth/hooks";
import { ApiError } from "@/lib/api/client";

import { createSubmission, diagnoseSubmission, fetchSubmission } from "./api";
import type {
  SubmissionDetail,
  SubmissionDiagnosis,
  SubmissionLanguage
} from "./types";

export function getSubmissionErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后再提交代码。";
  }
  if (error instanceof ApiError) {
    const messages: Record<string, string> = {
      CODE_EXECUTION_DISABLED: "当前未启用代码执行。请在安全 Judge 环境准备完成后再启用。",
      JUDGE_CONFIG_MISSING: "判题服务尚未配置。",
      JUDGE_UNAVAILABLE: "判题服务暂时不可用，请稍后重试。",
      JUDGE_TIMEOUT: "本次判题请求超时，请稍后重试。",
      JUDGE_BUSY: "判题服务正在处理其他提交，请稍后重试。",
      JUDGE_INVALID_RESPONSE: "判题服务返回了无效结果。",
      PROBLEM_NOT_FOUND: "题目不存在，或你没有访问权限。",
      PROBLEM_TEST_CASES_REQUIRED: "该题目没有测试用例，暂时无法判题。",
      SUBMISSION_NOT_FOUND: "提交记录不存在，或你没有访问权限。",
      SUBMISSION_DIAGNOSIS_NOT_AVAILABLE: "当前判题结果不支持 AI 失败诊断。",
      AI_CONFIG_MISSING: "当前未配置 AI 服务，请先进入系统设置完成配置。",
      AI_PROVIDER_TIMEOUT: "AI 服务响应超时，请稍后重试。",
      AI_PROVIDER_ERROR: "AI 服务暂时返回错误，请稍后重试。",
      PROMPT_TEMPLATE_NOT_FOUND: "AI 诊断模板尚未初始化，请先运行 Prompt 模板 seed。"
    };
    return messages[error.code] ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

export function useCreateSubmission() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (payload: { problem_id: string; language: SubmissionLanguage; source_code: string }) => {
      setLoading(true);
      setError(null);
      try {
        return await createSubmission(payload);
      } catch (err) {
        setError(getSubmissionErrorMessage(err));
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return { submit, loading, error };
}

export function useSubmission(id: string) {
  const [data, setData] = useState<SubmissionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    return fetchSubmission(id)
      .then((response) => setData(response.data))
      .catch((err: unknown) => setError(getSubmissionErrorMessage(err)))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  return { data, loading, error, reload: load };
}

export function useSubmissionDiagnosis(id: string) {
  const [data, setData] = useState<SubmissionDiagnosis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const response = await diagnoseSubmission(id);
      setData(response.data);
      return response;
    } catch (err) {
      setError(getSubmissionErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [id]);

  return { submit, data, loading, error };
}
