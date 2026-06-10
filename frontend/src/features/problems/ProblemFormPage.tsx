"use client";

import { FormEvent, type ReactNode, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { useTopics } from "@/features/topics/hooks";

import { useCreateProblem } from "./hooks";
import type { ProblemDetail, ProblemDifficulty, ProblemPayload } from "./types";

type FormState = {
  title: string;
  slug: string;
  source: string;
  source_url: string;
  difficulty: ProblemDifficulty;
  estimated_minutes: string;
  description_markdown: string;
  input_format: string;
  output_format: string;
  constraints: string;
  sample_input: string;
  sample_output: string;
  hint: string;
  solution_markdown: string;
  solution_code_cpp: string;
  solution_code_python: string;
  topic_ids: string[];
};

export const emptyProblemForm: FormState = {
  title: "",
  slug: "",
  source: "",
  source_url: "",
  difficulty: "beginner",
  estimated_minutes: "",
  description_markdown: "",
  input_format: "",
  output_format: "",
  constraints: "",
  sample_input: "",
  sample_output: "",
  hint: "",
  solution_markdown: "",
  solution_code_cpp: "",
  solution_code_python: "",
  topic_ids: []
};

const difficultyLabels: Record<ProblemDifficulty, string> = {
  beginner: "入门",
  basic: "基础",
  intermediate: "提高",
  advanced: "进阶"
};

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export function formStateFromProblem(problem: ProblemDetail): FormState {
  return {
    title: problem.title,
    slug: problem.slug,
    source: problem.source ?? "",
    source_url: problem.source_url ?? "",
    difficulty: problem.difficulty,
    estimated_minutes: problem.estimated_minutes?.toString() ?? "",
    description_markdown: problem.description_markdown,
    input_format: problem.input_format ?? "",
    output_format: problem.output_format ?? "",
    constraints: problem.constraints ?? "",
    sample_input: problem.sample_input ?? "",
    sample_output: problem.sample_output ?? "",
    hint: problem.hint ?? "",
    solution_markdown: problem.solution_markdown ?? "",
    solution_code_cpp: problem.solution_code_cpp ?? "",
    solution_code_python: problem.solution_code_python ?? "",
    topic_ids: problem.topic_tags.map((topic) => topic.id)
  };
}

export function payloadFromForm(state: FormState): ProblemPayload {
  return {
    title: state.title.trim(),
    slug: optionalText(state.slug),
    source: optionalText(state.source),
    source_url: optionalText(state.source_url),
    difficulty: state.difficulty,
    estimated_minutes: state.estimated_minutes ? Number(state.estimated_minutes) : null,
    description_markdown: state.description_markdown.trim(),
    input_format: optionalText(state.input_format),
    output_format: optionalText(state.output_format),
    constraints: optionalText(state.constraints),
    sample_input: optionalText(state.sample_input),
    sample_output: optionalText(state.sample_output),
    hint: optionalText(state.hint),
    solution_markdown: optionalText(state.solution_markdown),
    solution_code_cpp: optionalText(state.solution_code_cpp),
    solution_code_python: optionalText(state.solution_code_python),
    topic_ids: state.topic_ids
  };
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  type?: string;
}) {
  return (
    <label className="block text-sm font-semibold text-[#334155]">
      {label}
      <input
        className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none transition focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        type={type}
        value={value}
      />
    </label>
  );
}

function TextAreaField({
  label,
  value,
  onChange,
  placeholder,
  required = false,
  rows = 5,
  code = false
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
  rows?: number;
  code?: boolean;
}) {
  return (
    <label className="block text-sm font-semibold text-[#334155]">
      {label}
      <textarea
        className={`mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 leading-7 text-[#0f172a] outline-none transition focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] ${
          code ? "font-mono text-sm" : ""
        }`}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        rows={rows}
        value={value}
      />
    </label>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
      <h2 className="text-lg font-semibold text-[#0f172a]">{title}</h2>
      <div className="mt-4 grid gap-4">{children}</div>
    </section>
  );
}

export function ProblemForm({
  state,
  setState,
  submitLabel,
  loading,
  error,
  success,
  onSubmit,
  extraActions
}: {
  state: FormState;
  setState: (state: FormState) => void;
  submitLabel: string;
  loading: boolean;
  error: string | null;
  success?: string | null;
  onSubmit: (event: FormEvent) => void;
  extraActions?: ReactNode;
}) {
  const { data: topicsData, error: topicsError } = useTopics();
  const topics = topicsData?.data ?? [];

  function patch(update: Partial<FormState>) {
    setState({ ...state, ...update });
  }

  return (
    <form className="grid gap-5" onSubmit={onSubmit}>
      {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">{error}</p> : null}
      {success ? (
        <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-700">
          {success}
        </p>
      ) : null}
      {topicsError ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-700">
          知识点加载失败：{topicsError}
        </p>
      ) : null}

      <Section title="基本信息">
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="题目标题" onChange={(title) => patch({ title })} required value={state.title} />
          <TextField
            label="Slug 标识"
            onChange={(slug) => patch({ slug })}
            placeholder="留空则创建时自动生成"
            value={state.slug}
          />
          <label className="block text-sm font-semibold text-[#334155]">
            难度
            <select
              className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none transition focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              onChange={(event) => patch({ difficulty: event.target.value as ProblemDifficulty })}
              value={state.difficulty}
            >
              {Object.entries(difficultyLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <TextField
            label="预计用时（分钟）"
            onChange={(estimated_minutes) => patch({ estimated_minutes })}
            type="number"
            value={state.estimated_minutes}
          />
          <TextField label="来源" onChange={(source) => patch({ source })} value={state.source} />
          <TextField label="来源链接" onChange={(source_url) => patch({ source_url })} value={state.source_url} />
        </div>
        <label className="block text-sm font-semibold text-[#334155]">
          关联知识点
          <select
            className="mt-2 min-h-32 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none transition focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
            multiple
            onChange={(event) =>
              patch({
                topic_ids: Array.from(event.target.selectedOptions).map((option) => option.value)
              })
            }
            value={state.topic_ids}
          >
            {topics.map((topic) => (
              <option key={topic.id} value={topic.id}>
                {topic.category} / {topic.title}
              </option>
            ))}
          </select>
        </label>
      </Section>

      <Section title="题目描述">
        <TextAreaField
          label="题目描述"
          onChange={(description_markdown) => patch({ description_markdown })}
          required
          rows={8}
          value={state.description_markdown}
        />
        <TextAreaField label="数据范围" onChange={(constraints) => patch({ constraints })} value={state.constraints} />
      </Section>

      <Section title="输入输出与样例">
        <div className="grid gap-4 md:grid-cols-2">
          <TextAreaField label="输入格式" onChange={(input_format) => patch({ input_format })} value={state.input_format} />
          <TextAreaField label="输出格式" onChange={(output_format) => patch({ output_format })} value={state.output_format} />
          <TextAreaField code label="样例输入" onChange={(sample_input) => patch({ sample_input })} value={state.sample_input} />
          <TextAreaField code label="样例输出" onChange={(sample_output) => patch({ sample_output })} value={state.sample_output} />
        </div>
      </Section>

      <Section title="题解与代码">
        <TextAreaField label="提示" onChange={(hint) => patch({ hint })} rows={4} value={state.hint} />
        <TextAreaField label="题解思路" onChange={(solution_markdown) => patch({ solution_markdown })} rows={7} value={state.solution_markdown} />
        <div className="grid gap-4 md:grid-cols-2">
          <TextAreaField code label="C++ 参考代码" onChange={(solution_code_cpp) => patch({ solution_code_cpp })} rows={8} value={state.solution_code_cpp} />
          <TextAreaField code label="Python 参考代码" onChange={(solution_code_python) => patch({ solution_code_python })} rows={8} value={state.solution_code_python} />
        </div>
      </Section>

      <div className="flex flex-wrap items-center gap-3">
        <button
          className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
          disabled={loading}
          type="submit"
        >
          {loading ? "正在保存..." : submitLabel}
        </button>
        {extraActions}
        <Link
          className="rounded-md border border-[#bfdbfe] bg-white px-5 py-3 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
          href="/problems"
        >
          返回题库
        </Link>
      </div>
    </form>
  );
}

export function ProblemFormPage() {
  const router = useRouter();
  const { submit, loading, error } = useCreateProblem();
  const [state, setState] = useState<FormState>(emptyProblemForm);
  const canSubmit = useMemo(() => state.title.trim() && state.description_markdown.trim(), [state]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    try {
      const response = await submit(payloadFromForm(state));
      router.push(`/problems/${response.data.id}`);
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  return (
    <AppShell>
      <PageHeader
        description="手动录入练习题，整理输入输出、样例、提示和题解，形成自己的算法训练素材。"
        title="新建题目"
      />
      <ProblemForm
        error={error}
        loading={loading}
        onSubmit={(event) => void handleSubmit(event)}
        setState={setState}
        state={state}
        submitLabel="创建题目"
      />
    </AppShell>
  );
}
