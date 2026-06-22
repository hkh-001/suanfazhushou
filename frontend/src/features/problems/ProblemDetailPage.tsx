"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MarkdownContent } from "@/components/MarkdownContent";

import { difficultyLabels, difficultyStyles } from "./constants";
import { useProblem } from "./hooks";

type CopyState = "idle" | "copied" | "error";

function hasContent(value: string | null | undefined): value is string {
  return Boolean(value?.trim());
}

function safeSourceUrl(value: string | null): string | null {
  if (!value) {
    return null;
  }
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:" ? url.toString() : null;
  } catch {
    return null;
  }
}

function sourceLabel(source: string | null) {
  if (!source) {
    return "手动创建";
  }
  if (source === "zip_import") {
    return "ZIP 导入";
  }
  if (source === "ai_generated") {
    return "AI 生成";
  }
  return "外部导入";
}

function ContentSection({ title, content }: { title: string; content: string }) {
  return (
    <section className="border-b border-slate-200 pb-8 last:border-b-0 last:pb-0">
      <h2 className="mb-5 text-xl font-semibold text-slate-950">{title}</h2>
      <MarkdownContent content={content} />
    </section>
  );
}

function SampleCodeBlock({ label, content }: { label: string; content: string }) {
  const [copyState, setCopyState] = useState<CopyState>("idle");

  async function copy() {
    try {
      if (!navigator.clipboard) {
        throw new Error("Clipboard API unavailable");
      }
      await navigator.clipboard.writeText(content);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
    window.setTimeout(() => setCopyState("idle"), 1500);
  }

  const buttonLabel =
    copyState === "copied" ? "已复制" : copyState === "error" ? "复制失败" : "复制";

  return (
    <section className="min-w-0">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="font-semibold text-slate-900">{label}</h3>
        <button
          aria-label={`复制${label}`}
          className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 outline-none transition hover:border-blue-300 hover:text-blue-700 focus-visible:ring-2 focus-visible:ring-blue-300"
          onClick={() => void copy()}
          type="button"
        >
          {buttonLabel}
        </button>
      </div>
      <pre className="hljs max-h-80 overflow-auto whitespace-pre rounded-lg border border-slate-200 bg-slate-50 p-4 font-mono text-sm leading-6 text-slate-800 shadow-inner shadow-slate-100">
        <code>{content}</code>
      </pre>
    </section>
  );
}

export function ProblemDetailPage({ id }: { id: string }) {
  const { data, loading, error, reload } = useProblem(id);

  if (loading) {
    return (
      <AppShell>
        <section className="rounded-lg border border-blue-100 bg-white p-6 text-slate-500 shadow-sm">
          正在加载题目...
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">题目加载失败</p>
          <p className="mt-2 text-sm">{error ?? "题目不存在，或你没有访问权限。"}</p>
          <button
            className="mt-4 font-semibold text-blue-700 underline-offset-4 hover:underline"
            onClick={() => void reload()}
            type="button"
          >
            重试
          </button>
        </section>
      </AppShell>
    );
  }

  const sourceUrl = safeSourceUrl(data.source_url);
  const hasSolution =
    hasContent(data.solution_code_cpp) ||
    hasContent(data.solution_code_python) ||
    hasContent(data.solution_markdown);

  return (
    <AppShell>
      <header className="mb-7 overflow-hidden rounded-lg border border-blue-200 bg-white shadow-sm">
        <div className="border-l-4 border-blue-600 px-5 py-6 sm:px-7">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">
                个人题库
              </p>
              <h1 className="mt-2 break-words text-3xl font-semibold text-slate-950 sm:text-4xl">
                P{data.display_id} {data.title}
              </h1>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-sm">
                <span
                  className={`rounded-full border px-3 py-1 font-semibold ${difficultyStyles[data.difficulty]}`}
                >
                  {difficultyLabels[data.difficulty]}
                </span>
                {data.estimated_minutes ? (
                  <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-600">
                    预计 {data.estimated_minutes} 分钟
                  </span>
                ) : null}
                <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-slate-600">
                  来源：{sourceLabel(data.source)}
                </span>
                {data.is_ai_generated ? (
                  <span className="rounded-full border border-cyan-200 bg-cyan-50 px-3 py-1 font-semibold text-cyan-700">
                    AI 生成
                  </span>
                ) : null}
              </div>
            </div>
            <div className="flex shrink-0 flex-wrap gap-3">
              <Link
                className="rounded-md bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white outline-none transition hover:bg-blue-700 focus-visible:ring-2 focus-visible:ring-blue-300"
                href={`/problems/${id}/submit`}
              >
                提交代码
              </Link>
              <Link
                className="rounded-md border border-blue-200 bg-white px-5 py-2.5 text-sm font-semibold text-blue-700 outline-none transition hover:bg-blue-50 focus-visible:ring-2 focus-visible:ring-blue-300"
                href={`/problems/${id}/edit`}
              >
                编辑题目
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,3fr)_minmax(260px,1fr)]">
        <article className="min-w-0 space-y-8 rounded-lg border border-slate-200 bg-white p-5 shadow-sm sm:p-8">
          <ContentSection content={data.description_markdown} title="题目描述" />
          {hasContent(data.input_format) ? (
            <ContentSection content={data.input_format} title="输入格式" />
          ) : null}
          {hasContent(data.output_format) ? (
            <ContentSection content={data.output_format} title="输出格式" />
          ) : null}
          {hasContent(data.constraints) ? (
            <ContentSection content={data.constraints} title="数据范围" />
          ) : null}
          {hasContent(data.sample_input) || hasContent(data.sample_output) ? (
            <section className="border-b border-slate-200 pb-8">
              <h2 className="mb-5 text-xl font-semibold text-slate-950">样例</h2>
              <div className="grid gap-5 xl:grid-cols-2">
                {hasContent(data.sample_input) ? (
                  <SampleCodeBlock content={data.sample_input} label="样例输入" />
                ) : null}
                {hasContent(data.sample_output) ? (
                  <SampleCodeBlock content={data.sample_output} label="样例输出" />
                ) : null}
              </div>
            </section>
          ) : null}
          {hasContent(data.hint) ? <ContentSection content={data.hint} title="提示" /> : null}
        </article>

        <aside className="grid min-w-0 gap-5 lg:sticky lg:top-24">
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-lg font-semibold text-slate-950">题目信息</h2>
            <dl className="mt-5 grid gap-4 text-sm">
              <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
                <dt className="text-slate-500">题目编号</dt>
                <dd className="font-semibold text-slate-900">P{data.display_id}</dd>
              </div>
              <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
                <dt className="text-slate-500">难度</dt>
                <dd className="font-semibold text-slate-900">{difficultyLabels[data.difficulty]}</dd>
              </div>
              {data.estimated_minutes ? (
                <div className="flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
                  <dt className="text-slate-500">预计用时</dt>
                  <dd className="font-semibold text-slate-900">{data.estimated_minutes} 分钟</dd>
                </div>
              ) : null}
              <div className="flex items-start justify-between gap-4">
                <dt className="text-slate-500">来源</dt>
                <dd className="max-w-[65%] break-words text-right font-semibold text-slate-900">
                  {sourceUrl ? (
                    <a
                      className="text-blue-600 underline-offset-4 hover:underline"
                      href={sourceUrl}
                      rel="noreferrer noopener"
                      target="_blank"
                    >
                      {sourceLabel(data.source)}
                    </a>
                  ) : (
                    sourceLabel(data.source)
                  )}
                </dd>
              </div>
            </dl>

            <div className="mt-6 border-t border-slate-100 pt-5">
              <h3 className="text-sm font-semibold text-slate-900">知识点</h3>
              {data.topic_tags.length ? (
                <div className="mt-3 flex flex-wrap gap-2">
                  {data.topic_tags.map((topic) => (
                    <span
                      className="rounded-md border border-blue-100 bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700"
                      key={topic.id}
                    >
                      {topic.category} / {topic.title}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-500">暂未关联知识点</p>
              )}
            </div>
          </section>

          {hasSolution ? (
            <details className="group rounded-lg border border-blue-200 bg-white shadow-sm">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 font-semibold text-slate-950 outline-none transition hover:bg-blue-50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-blue-300">
                <span>查看题解/标程</span>
                <span className="text-blue-600 transition group-open:rotate-180" aria-hidden="true">
                  ↓
                </span>
              </summary>
              <div className="space-y-6 border-t border-blue-100 px-5 py-5">
                {hasContent(data.solution_code_cpp) ? (
                  <div>
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">C++17 标程</h3>
                    <MarkdownContent content={`\`\`\`cpp\n${data.solution_code_cpp}\n\`\`\``} />
                  </div>
                ) : null}
                {hasContent(data.solution_code_python) ? (
                  <div>
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">Python 3.11 标程</h3>
                    <MarkdownContent content={`\`\`\`python\n${data.solution_code_python}\n\`\`\``} />
                  </div>
                ) : null}
                {hasContent(data.solution_markdown) ? (
                  <div>
                    <h3 className="mb-3 text-sm font-semibold text-slate-900">题解说明</h3>
                    <MarkdownContent content={data.solution_markdown} />
                  </div>
                ) : null}
              </div>
            </details>
          ) : null}
        </aside>
      </div>
    </AppShell>
  );
}
