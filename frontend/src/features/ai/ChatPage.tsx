"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";

import { submitChat } from "./api";
import { AIErrorNotice, FormShell, ResultPanel, TopicSelect, friendlyAIError } from "./shared";
import type { AIResponseData, ChatPayload } from "./types";

export function ChatPage() {
  const { data: topicsData, error: topicsError } = useTopics();
  const [topicId, setTopicId] = useState("");
  const [mode, setMode] = useState<ChatPayload["mode"]>("beginner");
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
      const response = await submitChat({
        topic_id: topicId || null,
        question,
        mode
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
      description="选择知识点后提问，AI 会结合当前知识点进行分步骤讲解。"
      eyebrow="AI TUTOR"
      title="AI 算法问答"
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
          学习模式
          <select
            className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            onChange={(event) => setMode(event.target.value as ChatPayload["mode"])}
            value={mode}
          >
            <option value="beginner">入门模式</option>
            <option value="advanced">进阶模式</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-[#334155]">
          输入你的问题
          <textarea
            className="mt-2 min-h-36 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 leading-7 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            maxLength={2000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="例如：二分查找为什么要注意边界？前缀和适合解决什么问题？"
            required
            value={question}
          />
        </label>
        <button
          className="w-fit rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1d4ed8] disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "正在发送..." : "发送问题"}
        </button>
        {error ? <AIErrorNotice message={error} /> : null}
      </form>
      {!result && !loading && !error ? (
        <p className="mt-6 text-sm text-[#64748b]">提交问题后，AI 回答会显示在这里。</p>
      ) : null}
      {result ? (
        <div className="mt-6">
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="AI 回答"
          />
        </div>
      ) : null}
    </FormShell>
  );
}
