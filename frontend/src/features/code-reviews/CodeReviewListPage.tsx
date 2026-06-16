"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useCodeReviews } from "./hooks";

function shortText(value: string, length = 120) {
  return value.length > length ? `${value.slice(0, length)}...` : value;
}

export function CodeReviewListPage() {
  const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useCodeReviews(page);

  return (
    <AppShell>
      <PageHeader
        actions={
          <Link
            className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href="/mistakes"
          >
            返回错题本
          </Link>
        }
        description="查看你显式保存过的 AI 代码诊断记录，并从中创建复盘笔记。"
        title="诊断记录"
      />

      {loading ? (
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b]">正在加载诊断记录...</section>
      ) : null}

      {error ? (
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">诊断记录加载失败</p>
          <p className="mt-2 text-sm">{error}</p>
          <button className="mt-4 rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white" onClick={() => void reload()} type="button">
            重试
          </button>
        </section>
      ) : null}

      {!loading && !error && data?.data.length === 0 ? (
        <section className="rounded-xl border border-dashed border-[#bfdbfe] bg-white/70 p-8 text-center text-[#64748b]">
          <p className="font-semibold text-[#334155]">还没有保存的代码诊断。</p>
          <Link className="mt-3 inline-block font-semibold text-[#2563eb]" href="/code-review">
            去诊断代码
          </Link>
        </section>
      ) : null}

      <div className="grid gap-4">
        {data?.data.map((item) => (
          <Link
            className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60 outline-none transition hover:border-[#93c5fd] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href={`/code-reviews/${item.id}`}
            key={item.id}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-[#2563eb]">{item.language === "cpp" ? "C++" : "Python"}</p>
                <h2 className="mt-1 text-lg font-semibold text-[#0f172a]">{item.question || "未填写补充问题"}</h2>
              </div>
              <p className="text-sm text-[#64748b]">{new Date(item.created_at).toLocaleString("zh-CN")}</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#475569]">{shortText(item.analysis_result)}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#64748b]">
              {item.topic ? <span className="rounded-full bg-[#eff6ff] px-3 py-1">{item.topic.title}</span> : null}
              {item.problem ? <span className="rounded-full bg-[#eff6ff] px-3 py-1">题目 #{item.problem.display_id}</span> : null}
            </div>
          </Link>
        ))}
      </div>

      {data && data.pagination.total_pages > 1 ? (
        <div className="mt-6 flex items-center justify-center gap-3">
          <button className="rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-sm font-semibold text-[#1d4ed8] disabled:opacity-50" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} type="button">
            上一页
          </button>
          <span className="text-sm text-[#64748b]">
            第 {data.pagination.page} / {data.pagination.total_pages} 页
          </span>
          <button className="rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-sm font-semibold text-[#1d4ed8] disabled:opacity-50" disabled={page >= data.pagination.total_pages} onClick={() => setPage((value) => value + 1)} type="button">
            下一页
          </button>
        </div>
      ) : null}
    </AppShell>
  );
}
