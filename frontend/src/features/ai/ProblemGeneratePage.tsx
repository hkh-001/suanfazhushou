"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";

import { submitProblemGeneration } from "./api";
import { AIErrorNotice, EmptyResult, FormShell, ResultPanel, TopicSelect, friendlyAIError } from "./shared";
import type { AIResponseData, ProblemGenerationPayload } from "./types";

export function ProblemGeneratePage() {
  const { data: topicsData, error: topicsError } = useTopics();
  const [topicId, setTopicId] = useState("");
  const [difficulty, setDifficulty] = useState<ProblemGenerationPayload["difficulty"]>("beginner");
  const [requirements, setRequirements] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResponseData | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await submitProblemGeneration({
        topic_id: topicId || null,
        difficulty,
        requirements: requirements || null
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
      description="根据知识点和难度生成一题原创练习题，用于课后巩固。"
      title="AI 题目生成"
    >
      <form
        className="grid gap-5 rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60"
        onSubmit={submit}
      >
        <p className="rounded-lg border border-[#bfdbfe] bg-[#eff6ff] p-3 text-sm font-semibold text-[#1d4ed8]">
          保存 AI 生成题到个人题库将在 Phase 7 支持。本页当前只负责生成题目。
        </p>
        {topicsError ? (
          <p className="text-sm font-semibold text-red-700">知识点加载失败：{topicsError}</p>
        ) : null}
        <TopicSelect onChange={setTopicId} topics={topicsData?.data ?? []} value={topicId} />
        <label className="block text-sm font-medium text-[#334155]">
          选择难度
          <select
            className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            onChange={(event) =>
              setDifficulty(event.target.value as ProblemGenerationPayload["difficulty"])
            }
            value={difficulty}
          >
            <option value="beginner">入门</option>
            <option value="basic">基础</option>
            <option value="intermediate">提高</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-[#334155]">
          补充要求
          <textarea
            className="mt-2 min-h-40 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 leading-7 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            maxLength={1500}
            onChange={(event) => setRequirements(event.target.value)}
            placeholder="可选：说明题目场景、数据范围风格，或希望重点练习的思路。"
            value={requirements}
          />
        </label>
        <button
          className="w-fit rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1d4ed8] disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "正在生成..." : "生成题目"}
        </button>
      </form>

      <section className="min-w-0">
        {error ? <AIErrorNotice message={error} /> : null}
        {!result && !loading && !error ? (
          <EmptyResult>
            <div>
              <p className="font-semibold text-[#334155]">等待生成题目</p>
              <p className="mt-2">生成后的题目描述、样例和题解思路会显示在这里。</p>
            </div>
          </EmptyResult>
        ) : null}
        {loading ? (
          <EmptyResult>
            <p>AI 正在生成练习题...</p>
          </EmptyResult>
        ) : null}
        {result ? (
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="生成结果"
          />
        ) : null}
      </section>
    </FormShell>
  );
}
