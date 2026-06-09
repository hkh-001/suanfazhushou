"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";
import { ApiError } from "@/lib/api/client";

import { submitCodeReview } from "./api";
import { FormShell, ResultPanel, TopicSelect } from "./shared";
import type { AIResponseData, CodeReviewPayload } from "./types";

function errorMessage(error: unknown) {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "Request failed";
}

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
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <FormShell
      description="Diagnose logic bugs and complexity risks without executing user code."
      eyebrow="Code Diagnosis"
      title="Review algorithm code"
    >
      <form className="grid gap-5 border border-[#d7d0c3] bg-white/80 p-5" onSubmit={submit}>
        {topicsError ? (
          <p className="text-sm font-semibold text-red-700">Failed to load topics: {topicsError}</p>
        ) : null}
        <TopicSelect onChange={setTopicId} topics={topicsData?.data ?? []} value={topicId} />
        <label className="block text-sm font-medium text-[#344250]">
          Language
          <select
            className="mt-2 w-full border border-[#c9c1b4] bg-white px-3 py-2"
            onChange={(event) => setLanguage(event.target.value as CodeReviewPayload["language"])}
            value={language}
          >
            <option value="cpp">C++</option>
            <option value="python">Python</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-[#344250]">
          Code
          <textarea
            className="mt-2 min-h-72 w-full border border-[#c9c1b4] bg-[#101820] px-3 py-3 font-mono text-sm leading-6 text-[#f5f1e8]"
            maxLength={12000}
            onChange={(event) => setCode(event.target.value)}
            placeholder="Paste C++ or Python code here."
            required
            value={code}
          />
        </label>
        <label className="block text-sm font-medium text-[#344250]">
          Question
          <input
            className="mt-2 w-full border border-[#c9c1b4] bg-white px-3 py-2"
            maxLength={1000}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Optional: describe the bug, WA, TLE, or concern."
            value={question}
          />
        </label>
        <button
          className="w-fit bg-[#1f2933] px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "Reviewing..." : "Review code"}
        </button>
        {error ? <p className="text-sm font-semibold text-red-700">{error}</p> : null}
      </form>
      {!result && !loading && !error ? (
        <p className="mt-6 text-sm text-[#50606f]">Diagnosis will appear here after submission.</p>
      ) : null}
      {result ? (
        <div className="mt-6">
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="Diagnosis"
          />
        </div>
      ) : null}
    </FormShell>
  );
}
