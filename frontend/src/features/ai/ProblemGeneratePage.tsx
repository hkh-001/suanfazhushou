"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";

import { submitProblemGeneration } from "./api";
import { AIErrorNotice, FormShell, ResultPanel, TopicSelect, friendlyAIError } from "./shared";
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
      eyebrow="PROBLEM GENERATION"
      title="AI 题目生成"
    >
      <form
        className="grid gap-5 rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60"
        onSubmit={submit}
      >
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
        {error ? <AIErrorNotice message={error} /> : null}
      </form>
      {!result && !loading && !error ? (
        <p className="mt-6 text-sm text-[#64748b]">生成后的题目会显示在这里。</p>
      ) : null}
      {result ? (
        <div className="mt-6">
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="生成结果"
          />
        </div>
      ) : null}
    </FormShell>
  );
}
