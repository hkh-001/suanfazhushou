"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";
import { ApiError } from "@/lib/api/client";

import { submitChat } from "./api";
import { FormShell, ResultPanel, TopicSelect } from "./shared";
import type { AIResponseData, ChatPayload } from "./types";

function errorMessage(error: unknown) {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "Request failed";
}

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
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <FormShell
      description="Ask for a step-by-step explanation with optional knowledge map context."
      eyebrow="AI Tutor"
      title="Ask AlgoMentor"
    >
      <form className="grid gap-5 border border-[#d7d0c3] bg-white/80 p-5" onSubmit={submit}>
        {topicsError ? (
          <p className="text-sm font-semibold text-red-700">Failed to load topics: {topicsError}</p>
        ) : null}
        <TopicSelect onChange={setTopicId} topics={topicsData?.data ?? []} value={topicId} />
        <label className="block text-sm font-medium text-[#344250]">
          Mode
          <select
            className="mt-2 w-full border border-[#c9c1b4] bg-white px-3 py-2"
            onChange={(event) => setMode(event.target.value as ChatPayload["mode"])}
            value={mode}
          >
            <option value="beginner">Beginner</option>
            <option value="advanced">Advanced</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-[#344250]">
          Question
          <textarea
            className="mt-2 min-h-36 w-full border border-[#c9c1b4] bg-white px-3 py-2 leading-7"
            maxLength={2000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask about an algorithm idea, use case, complexity, or pitfall."
            required
            value={question}
          />
        </label>
        <button
          className="w-fit bg-[#1f2933] px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "Asking..." : "Ask"}
        </button>
        {error ? <p className="text-sm font-semibold text-red-700">{error}</p> : null}
      </form>
      {!result && !loading && !error ? (
        <p className="mt-6 text-sm text-[#50606f]">AI answers will appear here after you submit a question.</p>
      ) : null}
      {result ? (
        <div className="mt-6">
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="Answer"
          />
        </div>
      ) : null}
    </FormShell>
  );
}
