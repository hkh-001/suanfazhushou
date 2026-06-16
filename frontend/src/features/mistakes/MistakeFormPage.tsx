"use client";

import Link from "next/link";
import { FormEvent, type ReactNode, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { useCodeReview } from "@/features/code-reviews/hooks";
import { useProblems } from "@/features/problems/hooks";
import { useTopics } from "@/features/topics/hooks";

import { useCreateMistakeNote } from "./hooks";
import type { MistakeNoteDetail, MistakeNotePayload, ReviewStatus } from "./types";

type FormState = {
  title: string;
  error_type: string;
  root_cause: string;
  wrong_code: string;
  fixed_code: string;
  fix_suggestion: string;
  ai_summary: string;
  user_reflection: string;
  review_status: ReviewStatus;
  topic_id: string;
  problem_id: string;
  code_review_id: string;
};

export const emptyMistakeForm: FormState = {
  title: "",
  error_type: "",
  root_cause: "",
  wrong_code: "",
  fixed_code: "",
  fix_suggestion: "",
  ai_summary: "",
  user_reflection: "",
  review_status: "open",
  topic_id: "",
  problem_id: "",
  code_review_id: ""
};

const statusLabels: Record<ReviewStatus, string> = {
  open: "待复盘",
  reviewing: "复盘中",
  resolved: "已解决"
};

function optionalText(value: string): string | null {
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

export function formStateFromMistake(note: MistakeNoteDetail): FormState {
  return {
    title: note.title,
    error_type: note.error_type ?? "",
    root_cause: note.root_cause,
    wrong_code: note.wrong_code ?? "",
    fixed_code: note.fixed_code ?? "",
    fix_suggestion: note.fix_suggestion ?? "",
    ai_summary: note.ai_summary ?? "",
    user_reflection: note.user_reflection ?? "",
    review_status: note.review_status,
    topic_id: note.topic_id ?? "",
    problem_id: note.problem_id ?? "",
    code_review_id: note.code_review_id ?? ""
  };
}

export function payloadFromMistakeForm(state: FormState): MistakeNotePayload {
  return {
    title: state.title.trim(),
    error_type: optionalText(state.error_type),
    root_cause: state.root_cause.trim(),
    wrong_code: optionalText(state.wrong_code),
    fixed_code: optionalText(state.fixed_code),
    fix_suggestion: optionalText(state.fix_suggestion),
    ai_summary: optionalText(state.ai_summary),
    user_reflection: optionalText(state.user_reflection),
    review_status: state.review_status,
    topic_id: optionalText(state.topic_id),
    problem_id: optionalText(state.problem_id),
    code_review_id: optionalText(state.code_review_id)
  };
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
      <h2 className="text-lg font-semibold text-[#0f172a]">{title}</h2>
      <div className="mt-4 grid gap-4">{children}</div>
    </section>
  );
}

function TextField({ label, value, onChange, required = false }: { label: string; value: string; onChange: (value: string) => void; required?: boolean }) {
  return (
    <label className="block text-sm font-semibold text-[#334155]">
      {label}
      <input className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]" onChange={(event) => onChange(event.target.value)} required={required} value={value} />
    </label>
  );
}

function TextAreaField({ label, value, onChange, required = false, rows = 5, code = false }: { label: string; value: string; onChange: (value: string) => void; required?: boolean; rows?: number; code?: boolean }) {
  return (
    <label className="block text-sm font-semibold text-[#334155]">
      {label}
      <textarea className={`mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 leading-7 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] ${code ? "font-mono text-sm" : ""}`} onChange={(event) => onChange(event.target.value)} required={required} rows={rows} value={value} />
    </label>
  );
}

export function MistakeForm({
  state,
  setState,
  onSubmit,
  submitLabel,
  loading,
  error,
  success,
  extraActions
}: {
  state: FormState;
  setState: (state: FormState) => void;
  onSubmit: (event: FormEvent) => void;
  submitLabel: string;
  loading: boolean;
  error: string | null;
  success?: string | null;
  extraActions?: ReactNode;
}) {
  const { data: topicsData, error: topicsError } = useTopics();
  const { data: problemsData, error: problemsError } = useProblems(1);

  function patch(update: Partial<FormState>) {
    setState({ ...state, ...update });
  }

  return (
    <form className="grid gap-5" onSubmit={onSubmit}>
      {error ? <p className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-semibold text-red-700">{error}</p> : null}
      {success ? <p className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-700">{success}</p> : null}
      {topicsError || problemsError ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm font-semibold text-amber-700">
          关联数据加载失败：{topicsError ?? problemsError}
        </p>
      ) : null}

      <Section title="基本信息">
        <div className="grid gap-4 md:grid-cols-2">
          <TextField label="复盘标题" onChange={(title) => patch({ title })} required value={state.title} />
          <TextField label="错误类型" onChange={(error_type) => patch({ error_type })} value={state.error_type} />
          <label className="block text-sm font-semibold text-[#334155]">
            复盘状态
            <select className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]" onChange={(event) => patch({ review_status: event.target.value as ReviewStatus })} value={state.review_status}>
              {Object.entries(statusLabels).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Section>

      <Section title="关联信息">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block text-sm font-semibold text-[#334155]">
            关联知识点
            <select className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a]" onChange={(event) => patch({ topic_id: event.target.value })} value={state.topic_id}>
              <option value="">不关联知识点</option>
              {(topicsData?.data ?? []).map((topic) => (
                <option key={topic.id} value={topic.id}>
                  {topic.category} / {topic.title}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm font-semibold text-[#334155]">
            关联题目
            <select className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a]" onChange={(event) => patch({ problem_id: event.target.value })} value={state.problem_id}>
              <option value="">不关联题目</option>
              {(problemsData?.data ?? []).map((problem) => (
                <option key={problem.id} value={problem.id}>
                  #{problem.display_id} {problem.title}
                </option>
              ))}
            </select>
          </label>
        </div>
        <TextField label="关联诊断记录 ID" onChange={(code_review_id) => patch({ code_review_id })} value={state.code_review_id} />
      </Section>

      <Section title="复盘内容">
        <TextAreaField label="根因分析" onChange={(root_cause) => patch({ root_cause })} required rows={5} value={state.root_cause} />
        <TextAreaField code label="错误代码" onChange={(wrong_code) => patch({ wrong_code })} rows={7} value={state.wrong_code} />
        <TextAreaField code label="修正代码" onChange={(fixed_code) => patch({ fixed_code })} rows={7} value={state.fixed_code} />
        <TextAreaField label="修复建议" onChange={(fix_suggestion) => patch({ fix_suggestion })} rows={5} value={state.fix_suggestion} />
        <TextAreaField label="AI 诊断摘要" onChange={(ai_summary) => patch({ ai_summary })} rows={6} value={state.ai_summary} />
        <TextAreaField label="个人反思" onChange={(user_reflection) => patch({ user_reflection })} rows={5} value={state.user_reflection} />
      </Section>

      <div className="flex flex-wrap items-center gap-3">
        <button className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 disabled:opacity-60" disabled={loading} type="submit">
          {loading ? "正在保存..." : submitLabel}
        </button>
        {extraActions}
        <Link className="rounded-md border border-[#bfdbfe] bg-white px-5 py-3 text-sm font-semibold text-[#1d4ed8]" href="/mistakes">
          返回错题本
        </Link>
      </div>
    </form>
  );
}

export function MistakeCreatePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const codeReviewId = searchParams.get("code_review_id") ?? "";
  const { data: codeReview } = useCodeReview(codeReviewId);
  const { submit, loading, error } = useCreateMistakeNote();
  const [state, setState] = useState<FormState>({ ...emptyMistakeForm, code_review_id: codeReviewId });
  const [prefilled, setPrefilled] = useState(false);
  const canSubmit = useMemo(() => state.title.trim() && state.root_cause.trim(), [state]);

  useEffect(() => {
    if (codeReview && !prefilled) {
      setState((current) => ({
        ...current,
        code_review_id: codeReview.id,
        topic_id: codeReview.topic_id ?? current.topic_id,
        problem_id: codeReview.problem_id ?? current.problem_id,
        wrong_code: codeReview.code,
        ai_summary: codeReview.analysis_result,
        title: current.title || "代码诊断复盘",
        root_cause: current.root_cause || "根据保存的代码诊断记录补充根因分析。"
      }));
      setPrefilled(true);
    }
  }, [codeReview, prefilled]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }
    try {
      const response = await submit(payloadFromMistakeForm(state));
      router.push(`/mistakes/${response.data.id}`);
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  return (
    <AppShell>
      <PageHeader description="记录错误根因、修复建议和个人反思，形成可复盘的错题资料。" title="新建复盘笔记" />
      <MistakeForm error={error} loading={loading} onSubmit={(event) => void handleSubmit(event)} setState={setState} state={state} submitLabel="创建复盘笔记" />
    </AppShell>
  );
}
