"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { useCurrentUser } from "@/features/auth/hooks";

import { difficultyLabels } from "./constants";
import { usePublicProblems } from "./hooks";

export function PublicProblemListPage() {
  const [page, setPage] = useState(1);
  const { user } = useCurrentUser();
  const { data, loading, error, reload } = usePublicProblems(page);

  return (
    <AppShell>
      <PageHeader
        actions={
          user?.role === "admin" ? (
            <Link
              className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href="/problems/new?visibility=public"
            >
              新建公共题目
            </Link>
          ) : null
        }
        description="查看面向所有登录用户开放的练习题。普通用户可以阅读和提交代码，只有 admin 可以维护公共题目。"
        title="公共题库"
      />

      {loading ? (
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
          正在加载公共题库...
        </section>
      ) : null}

      {error ? (
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">公共题库加载失败</p>
          <p className="mt-2 text-sm">{error}</p>
          <button
            className="mt-4 font-semibold text-[#1d4ed8] underline-offset-4 hover:underline"
            onClick={() => void reload()}
            type="button"
          >
            重试
          </button>
        </section>
      ) : null}

      {!loading && !error && data && data.data.length === 0 ? (
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-8 text-center shadow-sm shadow-blue-100/60">
          <h2 className="text-xl font-semibold text-[#0f172a]">还没有公共题目</h2>
          <p className="mt-3 text-[#64748b]">admin 创建公共题目后，所有登录用户都可以在这里查看和练习。</p>
        </section>
      ) : null}

      {!loading && !error && data && data.data.length > 0 ? (
        <div className="grid gap-4">
          {data.data.map((problem) => (
            <Link
              className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60 outline-none transition hover:-translate-y-0.5 hover:border-[#93c5fd] hover:shadow-md focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href={`/problems/public/${problem.id}`}
              key={problem.id}
            >
              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-[#dbeafe] px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
                      公共题 #{problem.display_id}
                    </span>
                    <h2 className="text-xl font-semibold text-[#0f172a]">{problem.title}</h2>
                  </div>
                  <p className="mt-2 text-sm text-[#64748b]">slug: {problem.slug}</p>
                </div>
                <div className="flex flex-wrap gap-2 text-xs font-semibold">
                  <span className="rounded-full bg-[#dbeafe] px-3 py-1 text-[#1d4ed8]">
                    {difficultyLabels[problem.difficulty] ?? problem.difficulty}
                  </span>
                  {problem.estimated_minutes ? (
                    <span className="rounded-full bg-[#eff6ff] px-3 py-1 text-[#334155]">
                      {problem.estimated_minutes} 分钟
                    </span>
                  ) : null}
                </div>
              </div>
              {problem.topic_tags.length > 0 ? (
                <div className="mt-4 flex flex-wrap gap-2">
                  {problem.topic_tags.map((topic) => (
                    <span
                      className="rounded-full border border-[#bfdbfe] bg-white px-3 py-1 text-xs font-semibold text-[#1d4ed8]"
                      key={topic.id}
                    >
                      {topic.category} / {topic.title}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm text-[#94a3b8]">暂未关联知识点</p>
              )}
            </Link>
          ))}

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#dbeafe] bg-white/90 p-4 text-sm text-[#475569]">
            <span>
              第 {data.pagination.page} / {Math.max(data.pagination.total_pages, 1)} 页，共 {data.pagination.total} 题
            </span>
            <div className="flex gap-2">
              <button
                className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 font-semibold text-[#1d4ed8] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
                type="button"
              >
                上一页
              </button>
              <button
                className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 font-semibold text-[#1d4ed8] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={!data.pagination.total_pages || page >= data.pagination.total_pages}
                onClick={() => setPage((current) => current + 1)}
                type="button"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
