"use client";

import { FormEvent, useState } from "react";

import { useTopics } from "@/features/topics/hooks";
import { ApiError } from "@/lib/api/client";

import { submitProblemGeneration } from "./api";
import { FormShell, ResultPanel, TopicSelect } from "./shared";
import type { AIResponseData, ProblemGenerationPayload } from "./types";

function errorMessage(error: unknown) {
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "Request failed";
}

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
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <FormShell
      description="Generate one original, license-safe practice problem as structured JSON."
      eyebrow="Problem Generation"
      title="Generate a practice problem"
    >
      <form className="grid gap-5 border border-[#d7d0c3] bg-white/80 p-5" onSubmit={submit}>
        {topicsError ? (
          <p className="text-sm font-semibold text-red-700">Failed to load topics: {topicsError}</p>
        ) : null}
        <TopicSelect onChange={setTopicId} topics={topicsData?.data ?? []} value={topicId} />
        <label className="block text-sm font-medium text-[#344250]">
          Difficulty
          <select
            className="mt-2 w-full border border-[#c9c1b4] bg-white px-3 py-2"
            onChange={(event) =>
              setDifficulty(event.target.value as ProblemGenerationPayload["difficulty"])
            }
            value={difficulty}
          >
            <option value="beginner">Beginner</option>
            <option value="basic">Basic</option>
            <option value="intermediate">Intermediate</option>
          </select>
        </label>
        <label className="block text-sm font-medium text-[#344250]">
          Requirements
          <textarea
            className="mt-2 min-h-40 w-full border border-[#c9c1b4] bg-white px-3 py-2 leading-7"
            maxLength={1500}
            onChange={(event) => setRequirements(event.target.value)}
            placeholder="Optional: ask for a specific pattern, story, or constraint style."
            value={requirements}
          />
        </label>
        <button
          className="w-fit bg-[#1f2933] px-5 py-3 text-sm font-semibold text-white disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "Generating..." : "Generate problem"}
        </button>
        {error ? <p className="text-sm font-semibold text-red-700">{error}</p> : null}
      </form>
      {!result && !loading && !error ? (
        <p className="mt-6 text-sm text-[#50606f]">Generated problem JSON will appear here.</p>
      ) : null}
      {result ? (
        <div className="mt-6">
          <ResultPanel
            inputTokens={result.usage.input_tokens}
            model={result.model}
            outputTokens={result.usage.output_tokens}
            promptType={result.prompt_type}
            result={result.result}
            title="Generated problem"
          />
        </div>
      ) : null}
    </FormShell>
  );
}
