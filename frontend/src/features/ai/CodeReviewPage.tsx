"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { useCreateCodeReview } from "@/features/code-reviews/hooks";
import type { CodeReviewDetail } from "@/features/code-reviews/types";
import { useTopics } from "@/features/topics/hooks";

import { submitCodeReview } from "./api";
import { AIErrorNotice, EmptyResult, FormShell, ResultPanel, TopicSelect, friendlyAIError } from "./shared";
import type { AIResponseData, CodeReviewPayload } from "./types";

export function CodeReviewPage() {
  const { data: topicsData, error: topicsError } = useTopics();
  const { submit: saveReview, loading: saving, error: saveError } = useCreateCodeReview();
  const [topicId, setTopicId] = useState("");
  const [language, setLanguage] = useState<CodeReviewPayload["language"]>("cpp");
  const [code, setCode] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResponseData | null>(null);
  const [savedReview, setSavedReview] = useState<CodeReviewDetail | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setSavedReview(null);
    try {
      const response = await submitCodeReview({
        topic_id: topicId || null,
        language,
        code,
        question: question || null
      });
      setResult(response.data);
    } catch (err) {
      setError(friendlyAIError(err));
    } finally {
      setLoading(false);
    }
  }

  async function saveCurrentReview() {
    if (!result) {
      return;
    }
    try {
      const response = await saveReview({
        topic_id: topicId || null,
        problem_id: null,
        language,
        question: question || null,
        code,
        analysis_result: result.result,
        model: result.model,
        prompt_type: result.prompt_type,
        input_tokens: result.usage.input_tokens,
        output_tokens: result.usage.output_tokens
      });
      setSavedReview(response.data);
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  return (
    <FormShell
      description="AI 会从算法思路、潜在错误、复杂度和修改建议几个角度分析你的代码。诊断结果只会在你点击保存后进入诊断记录。"
      gridClassName="lg:grid-cols-[420px_1fr]"
      title="代码诊断"
    >
      <form
        className="grid gap-5 rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60"
        onSubmit={submit}
      >
        {topicsError ? (
          <p className="text-sm font-semibold text-red-700">知识点加载失败：{topicsError}</p>
        ) : null}
        <TopicSelect onChange={setTopicId} topics={topicsData?.data ?? []} value={topicId} />
        <label className="block text-sm font-medium text-[#334155]">
          选择语言
          <select
            className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            onChange={(event) => setLanguage(event.target.value as CodeReviewPayload["language"])}
            value={language}
          >
            <option value="cpp">C++</option>
            <option value="python">Python</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-[#334155]">
          粘贴你的代码
          <textarea
            className="mt-2 min-h-72 w-full rounded-md border border-[#bfdbfe] bg-[#0f172a] px-3 py-3 font-mono text-sm leading-6 text-[#e0f2fe] outline-none focus:border-[#60a5fa] focus:ring-2 focus:ring-[#bfdbfe]"
            maxLength={12000}
            onChange={(event) => setCode(event.target.value)}
            placeholder="在这里粘贴 C++ 或 Python 代码。"
            required
            value={code}
          />
        </label>
        <label className="block text-sm font-medium text-[#334155]">
          补充说明，可选
          <input
            className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            maxLength={1000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：这段代码为什么会超时？边界条件哪里可能出错？"
            value={question}
          />
        </label>
        <button
          className="w-fit rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1d4ed8] disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "正在诊断..." : "开始诊断"}
        </button>
      </form>

      <section className="min-w-0 space-y-4">
        {error ? <AIErrorNotice message={error} /> : null}
        {!result && !loading && !error ? (
          <EmptyResult>
            <div>
              <p className="font-semibold text-[#334155]">等待代码诊断</p>
              <p className="mt-2">提交代码后，诊断结果会显示在这里。</p>
            </div>
          </EmptyResult>
        ) : null}
        {loading ? (
          <EmptyResult>
            <p>AI 正在分析代码...</p>
          </EmptyResult>
        ) : null}
        {result ? (
          <>
            <ResultPanel
              inputTokens={result.usage.input_tokens}
              model={result.model}
              outputTokens={result.usage.output_tokens}
              promptType={result.prompt_type}
              result={result.result}
              title="诊断结果"
            />
            <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-[#0f172a]">保存诊断</h2>
                  <p className="mt-1 text-sm text-[#64748b]">只有点击保存后，完整代码和 AI 分析结果才会写入诊断记录。</p>
                </div>
                <button
                  className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
                  disabled={saving || Boolean(savedReview)}
                  onClick={() => void saveCurrentReview()}
                  type="button"
                >
                  {saving ? "正在保存..." : savedReview ? "已保存" : "保存本次诊断"}
                </button>
              </div>
              {saveError ? <p className="mt-4 text-sm font-semibold text-red-700">{saveError}</p> : null}
              {savedReview ? (
                <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                  <p className="font-semibold">已保存诊断记录。</p>
                  <div className="mt-3 flex flex-wrap gap-3">
                    <Link className="rounded-md bg-[#2563eb] px-3 py-2 text-sm font-semibold text-white" href={`/code-reviews/${savedReview.id}`}>
                      查看诊断记录
                    </Link>
                    <Link className="rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-sm font-semibold text-[#1d4ed8]" href={`/mistakes/new?code_review_id=${savedReview.id}`}>
                      创建复盘笔记
                    </Link>
                  </div>
                </div>
              ) : null}
            </section>
          </>
        ) : null}
      </section>
    </FormShell>
  );
}
