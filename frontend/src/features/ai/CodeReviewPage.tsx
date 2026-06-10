"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";

import { submitCodeReview } from "./api";
import { AIErrorNotice, EmptyResult, FormShell, ResultPanel, TopicSelect, friendlyAIError } from "./shared";
import type { AIResponseData, CodeReviewPayload } from "./types";

export function CodeReviewPage() {
  const { data: topicsData, error: topicsError } = useTopics();
  const [topicId, setTopicId] = useState("");
  const [language, setLanguage] = useState<CodeReviewPayload["language"]>("cpp");
  const [code, setCode] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResponseData | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
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

  return (
    <FormShell
      description="AI 会从算法思路、潜在错误、复杂度和修改建议几个角度分析你的代码。"
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

      <section className="min-w-0">
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
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="诊断结果"
          />
        ) : null}
      </section>
    </FormShell>
  );
}
