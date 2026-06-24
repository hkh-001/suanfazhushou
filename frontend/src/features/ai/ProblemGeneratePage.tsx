"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { saveGeneratedProblem } from "@/features/problems/api";
import type { GeneratedProblemSavePayload, GeneratedProblemTestCase, ProblemDetail } from "@/features/problems/types";
import { useTopics } from "@/features/topics/hooks";
import { ApiError } from "@/lib/api/client";

import { submitProblemGeneration } from "./api";
import { AIErrorNotice, EmptyResult, FormShell, ResultPanel, TopicSelect, friendlyAIError } from "./shared";
import type { AIResponseData, ProblemGenerationPayload } from "./types";

type ParsedGeneratedProblem = Omit<GeneratedProblemSavePayload, "topic_id" | "difficulty" | "requirements">;

function nonEmptyString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed || null;
}

function optionalString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed || null;
}

function normalizeHints(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.filter((item): item is string => typeof item === "string").map((item) => item.trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    return value
      .split(/\r?\n/)
      .map((item) => item.replace(/^[-*]\s*/, "").trim())
      .filter(Boolean);
  }
  return [];
}

function normalizeTestCases(value: unknown): GeneratedProblemTestCase[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item, index): GeneratedProblemTestCase | null => {
      if (item === null || typeof item !== "object" || Array.isArray(item)) {
        return null;
      }
      const record = item as Record<string, unknown>;
      const input = nonEmptyString(record.input);
      const expectedOutput = nonEmptyString(record.expected_output) ?? nonEmptyString(record.output);
      if (!input || !expectedOutput) {
        return null;
      }
      return {
        name: optionalString(record.name) ?? `${index + 1}`.padStart(2, "0"),
        input,
        expected_output: expectedOutput,
        is_sample: typeof record.is_sample === "boolean" ? record.is_sample : index === 0
      };
    })
    .filter((item): item is GeneratedProblemTestCase => item !== null);
}

function parseGeneratedProblem(raw: string): ParsedGeneratedProblem | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }

  if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
    return null;
  }
  const record = parsed as Record<string, unknown>;
  const title = nonEmptyString(record.title);
  const statement = nonEmptyString(record.statement);
  const inputFormat = nonEmptyString(record.input_format);
  const outputFormat = nonEmptyString(record.output_format);
  const testCases = normalizeTestCases(record.test_cases);
  if (!title || !statement || !inputFormat || !outputFormat || testCases.length === 0) {
    return null;
  }
  const sampleCase = testCases.find((testCase) => testCase.is_sample) ?? testCases[0];

  return {
    title,
    statement,
    input_format: inputFormat,
    output_format: outputFormat,
    constraints: optionalString(record.constraints),
    sample_input: optionalString(record.sample_input) ?? sampleCase.input,
    sample_output: optionalString(record.sample_output) ?? sampleCase.expected_output,
    test_cases: testCases,
    hints: normalizeHints(record.hints),
    solution_idea: optionalString(record.solution_idea)
  };
}

function saveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "AUTH_REQUIRED" || error.code === "INVALID_SESSION" || error.code === "TOKEN_EXPIRED" || error.code === "TOKEN_INVALID") {
      return "请先登录后再保存到个人题库。";
    }
    if (error.code === "TOPIC_NOT_FOUND") {
      return "当前关联知识点不可用，请重新选择知识点后再保存。";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "保存失败，请稍后重试。";
}

function PreviewField({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) {
    return null;
  }
  return (
    <div>
      <dt className="text-xs font-semibold text-[#2563eb]">{label}</dt>
      <dd className="mt-1 whitespace-pre-wrap break-words text-sm leading-6 text-[#334155]">{value}</dd>
    </div>
  );
}

function TestCasePreview({ item, index }: { item: GeneratedProblemTestCase; index: number }) {
  return (
    <div className="rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <dt className="text-xs font-semibold text-[#2563eb]">
          测试用例 {item.name ?? `${index + 1}`.padStart(2, "0")}
        </dt>
        {item.is_sample ? (
          <span className="rounded-full bg-[#dbeafe] px-2 py-0.5 text-xs font-semibold text-[#1d4ed8]">样例</span>
        ) : null}
      </div>
      <dd className="mt-3 grid gap-3 md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold text-[#64748b]">输入</p>
          <pre className="mt-1 overflow-x-auto rounded-md border border-[#e2e8f0] bg-white p-3 text-xs leading-5 text-[#0f172a]">
            {item.input}
          </pre>
        </div>
        <div>
          <p className="text-xs font-semibold text-[#64748b]">期望输出</p>
          <pre className="mt-1 overflow-x-auto rounded-md border border-[#e2e8f0] bg-white p-3 text-xs leading-5 text-[#0f172a]">
            {item.expected_output}
          </pre>
        </div>
      </dd>
    </div>
  );
}

export function ProblemGeneratePage() {
  const { data: topicsData, error: topicsError } = useTopics();
  const [topicId, setTopicId] = useState("");
  const [difficulty, setDifficulty] = useState<ProblemGenerationPayload["difficulty"]>("beginner");
  const [requirements, setRequirements] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AIResponseData | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [savedProblem, setSavedProblem] = useState<ProblemDetail | null>(null);

  const parsedProblem = useMemo(() => (result ? parseGeneratedProblem(result.result) : null), [result]);
  const cannotSaveGeneratedResult = Boolean(result && !parsedProblem);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setSaveError(null);
    setSavedProblem(null);
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

  async function saveToProblemBank() {
    if (!parsedProblem) {
      return;
    }
    setSaving(true);
    setSaveError(null);
    setSavedProblem(null);
    try {
      const response = await saveGeneratedProblem({
        ...parsedProblem,
        topic_id: topicId || null,
        difficulty,
        requirements: requirements || null
      });
      setSavedProblem(response.data);
    } catch (err) {
      setSaveError(saveErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  function continueGenerating() {
    setResult(null);
    setSaveError(null);
    setSavedProblem(null);
  }

  return (
    <FormShell
      description="根据知识点和难度生成原创练习题，确认结果后可显式保存到个人题库。"
      title="AI 题目生成"
    >
      <form
        className="grid gap-5 rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60"
        onSubmit={submit}
      >
        <p className="rounded-lg border border-[#bfdbfe] bg-[#eff6ff] p-3 text-sm font-semibold text-[#1d4ed8]">
          生成结果不会自动保存。只有点击“保存到个人题库”后，题目才会进入你的个人题库。
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

      <section className="min-w-0 space-y-4">
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
          <>
            <ResultPanel
              inputTokens={result.usage.input_tokens}
              model={result.model}
              outputTokens={result.usage.output_tokens}
              promptType={result.prompt_type}
              result={result.result}
              title="生成结果"
            />
            {cannotSaveGeneratedResult ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-semibold text-amber-800">
                当前结果无法保存，请重新生成。原始 AI 输出仍可复制查看。
              </p>
            ) : null}
            {parsedProblem ? (
              <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
                <div className="flex flex-wrap items-start justify-between gap-3 border-b border-[#e2e8f0] pb-4">
                  <div>
                    <h2 className="text-lg font-semibold text-[#0f172a]">保存预览</h2>
                    <p className="mt-1 text-sm text-[#64748b]">确认结构化字段无误后，可以保存到个人题库。</p>
                  </div>
                  <button
                    className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1d4ed8] disabled:opacity-60"
                    disabled={saving || Boolean(savedProblem)}
                    onClick={() => void saveToProblemBank()}
                    type="button"
                  >
                    {saving ? "正在保存..." : savedProblem ? "已保存" : "保存到个人题库"}
                  </button>
                </div>
                <dl className="mt-4 grid gap-4">
                  <PreviewField label="题目标题" value={parsedProblem.title} />
                  <PreviewField label="题目描述" value={parsedProblem.statement} />
                  <PreviewField label="输入格式" value={parsedProblem.input_format} />
                  <PreviewField label="输出格式" value={parsedProblem.output_format} />
                  <PreviewField label="数据范围" value={parsedProblem.constraints} />
                  <PreviewField label="样例输入" value={parsedProblem.sample_input} />
                  <PreviewField label="样例输出" value={parsedProblem.sample_output} />
                  <div>
                    <dt className="text-xs font-semibold text-[#2563eb]">测试用例</dt>
                    <dd className="mt-2 grid gap-3">
                      {parsedProblem.test_cases.map((testCase, index) => (
                        <TestCasePreview
                          index={index}
                          item={testCase}
                          key={`${testCase.name ?? index}-${index}`}
                        />
                      ))}
                    </dd>
                  </div>
                  {parsedProblem.hints.length ? (
                    <div>
                      <dt className="text-xs font-semibold text-[#2563eb]">提示</dt>
                      <dd className="mt-1 whitespace-pre-wrap break-words text-sm leading-6 text-[#334155]">
                        {parsedProblem.hints.map((hint) => `- ${hint}`).join("\n")}
                      </dd>
                    </div>
                  ) : null}
                  <PreviewField label="题解思路" value={parsedProblem.solution_idea} />
                </dl>
                {saveError ? (
                  <p className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
                    {saveError}
                  </p>
                ) : null}
                {savedProblem ? (
                  <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
                    <p className="font-semibold">已保存到个人题库 #{savedProblem.display_id}</p>
                    <div className="mt-3 flex flex-wrap gap-3">
                      <Link
                        className="rounded-md bg-[#2563eb] px-3 py-2 text-sm font-semibold text-white outline-none hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                        href={`/problems/${savedProblem.id}`}
                      >
                        查看题目
                      </Link>
                      <button
                        className="rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                        onClick={continueGenerating}
                        type="button"
                      >
                        继续生成
                      </button>
                    </div>
                  </div>
                ) : null}
              </section>
            ) : null}
          </>
        ) : null}
      </section>
    </FormShell>
  );
}
