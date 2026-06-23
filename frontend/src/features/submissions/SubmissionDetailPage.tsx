"use client";

import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useSubmission } from "./hooks";

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

function metric(value: number | null, unit: string) {
  return value === null ? "暂无数据" : `${value} ${unit}`;
}

export function SubmissionDetailPage({ id }: { id: string }) {
  const { data, loading, error, reload } = useSubmission(id);

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
