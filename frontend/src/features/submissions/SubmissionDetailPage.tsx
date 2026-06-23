"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MarkdownContent } from "@/components/MarkdownContent";
import { PageHeader } from "@/components/PageHeader";
import { useCreateCodeReview } from "@/features/code-reviews/hooks";
import type { CodeReviewDetail } from "@/features/code-reviews/types";
import { AIErrorNotice } from "@/features/ai/shared";

import { useSubmission, useSubmissionDiagnosis } from "./hooks";

const verdictLabels: Record<string, string> = {
  accepted: "通过",
  wrong_answer: "答案错误",
  compile_error: "编译错误",
  runtime_error: "运行错误",
  time_limit_exceeded: "运行超时",
  memory_limit_exceeded: "内存超限",
  output_limit_exceeded: "输出超限",
  internal_error: "判题异常",
  not_run: "未执行"
};

const diagnosableVerdicts = new Set([
  "compile_error",
  "wrong_answer",
  "runtime_error",
  "time_limit_exceeded",
  "memory_limit_exceeded",
  "output_limit_exceeded"
]);

function metric(value: number | null, unit: string) {
  return value === null ? "暂无数据" : `${value} ${unit}`;
}

export function SubmissionDetailPage({ id }: { id: string }) {
  const { data, loading, error, reload } = useSubmission(id);
  const diagnosis = useSubmissionDiagnosis(id);
  const saveReview = useCreateCodeReview();
  const [savedReview, setSavedReview] = useState<CodeReviewDetail | null>(null);

  async function runDiagnosis() {
    setSavedReview(null);
    try {
      await diagnosis.submit();
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  async function saveDiagnosis() {
    if (!data || !diagnosis.data) {
      return;
    }
    try {
      const response = await saveReview.submit({
        problem_id: data.problem.id,
        language: data.language,
        code: data.source_code,
        analysis_result: diagnosis.data.result,
        model: diagnosis.data.model,
        prompt_type: diagnosis.data.prompt_type,
        input_tokens: diagnosis.data.usage.input_tokens,
        output_tokens: diagnosis.data.usage.output_tokens,
        question: `判题提交 ${data.id} 的 AI 失败诊断，原始 verdict：${data.verdict}`
      });
      setSavedReview(response.data);
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  if (loading) {
    return (
      <AppShell>
        <section className="rounded-lg border border-blue-100 bg-white p-6 text-slate-500">正在加载判题结果...</section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
          <p>{error ?? "提交记录不存在。"}</p>
          <button className="mt-4 font-semibold text-blue-700 hover:underline" onClick={() => void reload()} type="button">
            重试
          </button>
        </section>
      </AppShell>
    );
  }

  const accepted = data.verdict === "accepted";
  const canDiagnose = diagnosableVerdicts.has(data.verdict);

  return (
    <AppShell>
      <PageHeader
        actions={
          data.problem.id ? (
            <Link
              className="rounded-md border border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50"
              href={`/problems/${data.problem.id}`}
            >
              返回题目
            </Link>
          ) : undefined
        }
        description={`个人题库 #${data.problem.display_id}「${data.problem.title}」的判题记录`}
        title="判题结果"
      />

      <section
        className={`rounded-lg border p-6 ${
          accepted ? "border-emerald-200 bg-emerald-50" : "border-amber-200 bg-amber-50"
        }`}
      >
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold text-slate-500">最终结果</p>
            <h2 className={`mt-1 text-3xl font-semibold ${accepted ? "text-emerald-700" : "text-amber-800"}`}>
              {verdictLabels[data.verdict] ?? data.verdict}
            </h2>
          </div>
          <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm text-slate-600 sm:grid-cols-4">
            <span>语言：{data.language === "cpp" ? "C++17" : "Python 3.11"}</span>
            <span>通过：{data.passed_case_count}/{data.total_case_count}</span>
            <span>耗时：{metric(data.execution_time_ms, "ms")}</span>
            <span>内存：{metric(data.memory_kb, "KB")}</span>
          </div>
        </div>
        {data.error_message ? <p className="mt-4 text-sm text-slate-700">{data.error_message}</p> : null}
      </section>

      {data.compile_output ? (
        <section className="mt-6 rounded-lg border border-red-200 bg-white p-5">
          <h2 className="font-semibold text-slate-900">编译输出</h2>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md bg-slate-950 p-4 text-sm text-red-100">
            {data.compile_output}
          </pre>
        </section>
      ) : null}

      <section className="mt-6 overflow-hidden rounded-lg border border-blue-200 bg-white shadow-sm">
        <div className="border-b border-blue-100 bg-blue-50/70 px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-950">AI 失败诊断</h2>
              <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600">
                AI 只解释已经保存的 Judge 结果，不会重新运行代码或修改判题结论。诊断会发送源码和有限的失败上下文，可能产生少量模型调用费用。
              </p>
            </div>
            {canDiagnose && !diagnosis.data ? (
              <button
                className="rounded-md bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white outline-none transition hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-300 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={diagnosis.loading}
                onClick={() => void runDiagnosis()}
                type="button"
              >
                {diagnosis.loading ? "AI 正在分析..." : "AI 分析失败原因"}
              </button>
            ) : null}
          </div>
        </div>

        <div className="p-5">
          {accepted ? (
            <p className="text-sm text-emerald-700">本次提交已通过，无需进行失败诊断。</p>
          ) : null}
          {data.verdict === "internal_error" ? (
            <p className="text-sm text-amber-700">
              本次结果属于判题基础设施异常，不使用 AI 推测用户代码原因。请稍后重新提交或检查 Judge 服务。
            </p>
          ) : null}
          {diagnosis.error ? <AIErrorNotice message={diagnosis.error} /> : null}
          {diagnosis.loading ? (
            <div className="rounded-md border border-dashed border-blue-200 bg-blue-50/40 px-4 py-8 text-center text-sm text-slate-600">
              正在结合判题结果分析源码，请稍候...
            </div>
          ) : null}
          {canDiagnose && !diagnosis.loading && !diagnosis.data && !diagnosis.error ? (
            <p className="text-sm text-slate-500">
              诊断不会自动触发，也不会自动保存。点击上方按钮后才会调用 AI 服务。
            </p>
          ) : null}
          {diagnosis.data ? (
            <div className="space-y-5">
              {diagnosis.data.context_info.code_truncated ? (
                <p className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                  源码超过 AI 上下文限制，本次仅分析了源码首尾片段。
                </p>
              ) : null}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-3 text-xs text-slate-500">
                  <span>模型：{diagnosis.data.model}</span>
                  <span>失败测试点上下文：{diagnosis.data.context_info.failed_case_count_included} 个</span>
                  <span>
                    题目上下文：
                    {diagnosis.data.context_info.problem_context_included ? "已包含" : "仅使用题目快照"}
                  </span>
                  <span>
                    Token：{diagnosis.data.usage.input_tokens ?? "-"} / {diagnosis.data.usage.output_tokens ?? "-"}
                  </span>
                </div>
                <button
                  className="rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 outline-none transition hover:border-blue-200 hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-300"
                  onClick={() => void runDiagnosis()}
                  type="button"
                >
                  重新诊断
                </button>
              </div>
              <MarkdownContent content={diagnosis.data.result} />
              <div className="border-t border-slate-200 pt-5">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h3 className="font-semibold text-slate-900">保存诊断记录</h3>
                    <p className="mt-1 text-sm text-slate-500">
                      只有再次明确点击保存后，完整源码和 AI 诊断才会写入诊断记录。
                    </p>
                  </div>
                  <button
                    className="rounded-md border border-blue-200 bg-white px-4 py-2.5 text-sm font-semibold text-blue-700 outline-none transition hover:bg-blue-50 focus-visible:ring-2 focus-visible:ring-blue-300 disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={saveReview.loading || Boolean(savedReview)}
                    onClick={() => void saveDiagnosis()}
                    type="button"
                  >
                    {saveReview.loading ? "正在保存..." : savedReview ? "已保存" : "保存诊断记录"}
                  </button>
                </div>
                {saveReview.error ? (
                  <p className="mt-3 text-sm font-semibold text-red-700">{saveReview.error}</p>
                ) : null}
                {savedReview ? (
                  <div className="mt-4 flex flex-wrap gap-3 rounded-md border border-emerald-200 bg-emerald-50 px-4 py-3">
                    <Link
                      className="rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white"
                      href={`/code-reviews/${savedReview.id}`}
                    >
                      查看诊断记录
                    </Link>
                    <Link
                      className="rounded-md border border-blue-200 bg-white px-3 py-2 text-sm font-semibold text-blue-700"
                      href={`/mistakes/new?code_review_id=${savedReview.id}`}
                    >
                      创建复盘笔记
                    </Link>
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      </section>

      <section className="mt-6 rounded-lg border border-blue-100 bg-white p-5">
        <h2 className="font-semibold text-slate-900">测试点结果</h2>
        {data.case_results.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">本次提交没有可展示的测试点结果。</p>
        ) : (
          <div className="mt-4 grid gap-4">
            {data.case_results.map((item) => (
              <article className="rounded-md border border-slate-200 p-4" key={item.case_index}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="font-semibold text-slate-900">
                    {item.is_sample ? `样例 ${item.name ?? item.case_index}` : `隐藏测试点 #${item.case_index}`}
                  </h3>
                  <div className="flex flex-wrap gap-3 text-sm text-slate-600">
                    <span>{verdictLabels[item.verdict] ?? item.verdict}</span>
                    <span>{metric(item.execution_time_ms, "ms")}</span>
                    <span>{metric(item.memory_kb, "KB")}</span>
                  </div>
                </div>
                {item.verdict === "not_run" ? (
                  <p className="mt-3 text-sm text-amber-700">因达到本次判题总时间限制，未执行该测试点。</p>
                ) : null}
                {item.error_message ? <p className="mt-3 text-sm text-red-700">{item.error_message}</p> : null}
                {item.is_sample ? (
                  <div className="mt-4 grid gap-3 lg:grid-cols-3">
                    {[
                      ["输入", item.input_text],
                      ["期望输出", item.expected_output_text],
                      ["实际输出", item.actual_output]
                    ].map(([label, value]) => (
                      <div className="min-w-0" key={label}>
                        <p className="text-xs font-semibold text-slate-500">{label}</p>
                        <pre className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap break-words rounded-md bg-slate-950 p-3 text-xs text-slate-100">
                          {value || "（空）"}
                        </pre>
                      </div>
                    ))}
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="mt-6 rounded-lg border border-blue-100 bg-white p-5">
        <h2 className="font-semibold text-slate-900">提交源码</h2>
        <pre className="mt-3 max-h-[520px] overflow-auto whitespace-pre-wrap break-words rounded-md bg-slate-950 p-5 font-mono text-sm leading-6 text-slate-100">
          {data.source_code}
        </pre>
      </section>
    </AppShell>
  );
}
