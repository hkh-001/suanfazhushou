"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useMistakeNotes } from "./hooks";
import type { ReviewStatus } from "./types";

const statusLabels: Record<ReviewStatus, string> = {
  open: "待复盘",
  reviewing: "复盘中",
  resolved: "已解决"
};

export function MistakeListPage() {
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<ReviewStatus | "all">("all");
  const { data, loading, error, reload } = useMistakeNotes(page, status);

  function changeStatus(nextStatus: ReviewStatus | "all") {
    setStatus(nextStatus);
    setPage(1);
  }

  return (
    <AppShell>
      <PageHeader
        actions={
          <>
            <Link className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8]" href="/code-reviews">
              诊断记录
            </Link>
            <Link className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white" href="/mistakes/new">
              新建复盘
            </Link>
          </>
        }
        description="管理你显式保存的错误复盘、根因分析和修复建议。"
        title="错题本"
      />

      <div className="mb-5 flex flex-wrap gap-2">
        {(["all", "open", "reviewing", "resolved"] as const).map((item) => (
          <button
            className={`rounded-md px-4 py-2 text-sm font-semibold ${status === item ? "bg-[#2563eb] text-white" : "border border-[#bfdbfe] bg-white text-[#1d4ed8]"}`}
            key={item}
            onClick={() => changeStatus(item)}
            type="button"
          >
            {item === "all" ? "全部" : statusLabels[item]}
          </button>
        ))}
      </div>

      {loading ? <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b]">正在加载错题本...</section> : null}
      {error ? (
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">错题本加载失败</p>
          <p className="mt-2 text-sm">{error}</p>
          <button className="mt-4 rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white" onClick={() => void reload()} type="button">
            重试
          </button>
        </section>
      ) : null}
      {!loading && !error && data?.data.length === 0 ? (
        <section className="rounded-xl border border-dashed border-[#bfdbfe] bg-white/70 p-8 text-center text-[#64748b]">
          <p className="font-semibold text-[#334155]">还没有复盘笔记。</p>
          <Link className="mt-3 inline-block font-semibold text-[#2563eb]" href="/mistakes/new">
            新建第一条复盘
          </Link>
        </section>
      ) : null}

      <div className="grid gap-4">
        {data?.data.map((item) => (
          <Link
            className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60 outline-none transition hover:border-[#93c5fd] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href={`/mistakes/${item.id}`}
            key={item.id}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-[#2563eb]">{statusLabels[item.review_status]}</p>
                <h2 className="mt-1 text-lg font-semibold text-[#0f172a]">{item.title}</h2>
              </div>
              <p className="text-sm text-[#64748b]">{new Date(item.created_at).toLocaleString("zh-CN")}</p>
            </div>
            <p className="mt-3 text-sm leading-6 text-[#475569]">{item.root_cause}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-[#64748b]">
              {item.error_type ? <span className="rounded-full bg-[#eff6ff] px-3 py-1">{item.error_type}</span> : null}
              {item.topic ? <span className="rounded-full bg-[#eff6ff] px-3 py-1">{item.topic.title}</span> : null}
              {item.problem ? <span className="rounded-full bg-[#eff6ff] px-3 py-1">题目 #{item.problem.display_id}</span> : null}
              {item.code_review ? <span className="rounded-full bg-[#eff6ff] px-3 py-1">来自诊断记录</span> : null}
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
