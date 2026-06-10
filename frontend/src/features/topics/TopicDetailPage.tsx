"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";

import { useTopic, useUpdateLearningRecord } from "./hooks";
import type { LearningRecordPayload } from "./types";

const statusOptions: LearningRecordPayload["status"][] = ["not_started", "learning", "mastered"];
const statusLabels: Record<LearningRecordPayload["status"], string> = {
  not_started: "未开始",
  learning: "学习中",
  mastered: "已掌握"
};

export function TopicDetailPage({ id }: { id: string }) {
  const { data, loading, error, reload } = useTopic(id);
  const { update, loading: saving, error: saveError, success } = useUpdateLearningRecord();
  const [selectedStatus, setSelectedStatus] = useState<LearningRecordPayload["status"]>("not_started");

  useEffect(() => {
    if (data) {
      setSelectedStatus(data.learning_status.status);
    }
  }, [data]);

  if (loading) {
    return (
      <AppShell maxWidth="max-w-6xl">
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
          正在加载知识点详情...
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell maxWidth="max-w-6xl">
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <Link className="font-semibold text-[#1d4ed8] underline-offset-4 hover:underline" href="/topics">
            返回知识地图
          </Link>
          <p className="mt-6 font-semibold">知识点加载失败</p>
          <p className="mt-2 text-sm">{error ?? "未找到该知识点。"}</p>
        </section>
      </AppShell>
    );
  }

  const topic = data;

  async function submitStatus() {
    const progress = selectedStatus === "mastered" ? 100 : selectedStatus === "learning" ? 50 : 0;
    const mastery = selectedStatus === "mastered" ? 5 : selectedStatus === "learning" ? 2 : 0;
    await update({
      topic_id: topic.id,
      status: selectedStatus,
      progress_percent: progress,
      mastery_level: mastery,
      note: null
    });
    await reload();
  }

  return (
    <AppShell maxWidth="max-w-6xl">
      <div className="grid gap-6 lg:grid-cols-[300px_1fr]">
        <aside className="space-y-4 lg:sticky lg:top-24 lg:self-start">
          <Link
            className="inline-flex rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href="/topics"
          >
            返回知识地图
          </Link>

          <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-lg font-semibold text-[#0f172a]">知识点信息</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div>
                <dt className="text-[#64748b]">分类</dt>
                <dd className="mt-1 font-semibold text-[#0f172a]">{topic.category}</dd>
              </div>
              <div>
                <dt className="text-[#64748b]">阶段</dt>
                <dd className="mt-1 font-semibold text-[#0f172a]">{topic.level}</dd>
              </div>
              <div>
                <dt className="text-[#64748b]">难度</dt>
                <dd className="mt-1 font-semibold text-[#0f172a]">{topic.difficulty_score}/10</dd>
              </div>
              <div>
                <dt className="text-[#64748b]">预计用时</dt>
                <dd className="mt-1 font-semibold text-[#0f172a]">{topic.estimated_minutes} 分钟</dd>
              </div>
              <div>
                <dt className="text-[#64748b]">当前状态</dt>
                <dd className="mt-1 font-semibold text-[#0f172a]">
                  {statusLabels[topic.learning_status.status]}
                </dd>
              </div>
            </dl>
          </section>

          <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-lg font-semibold text-[#0f172a]">学习状态</h2>
            <div className="mt-4 grid gap-2">
              {statusOptions.map((status) => (
                <button
                  className={`rounded-md border px-3 py-2 text-sm font-semibold outline-none transition focus-visible:ring-2 focus-visible:ring-[#93c5fd] ${
                    selectedStatus === status
                      ? "border-[#2563eb] bg-[#2563eb] text-white"
                      : "border-[#bfdbfe] bg-white text-[#1d4ed8] hover:bg-[#eff6ff]"
                  }`}
                  key={status}
                  onClick={() => setSelectedStatus(status)}
                  type="button"
                >
                  {statusLabels[status]}
                </button>
              ))}
            </div>
            <button
              className="mt-4 w-full rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
              disabled={saving}
              onClick={() => void submitStatus()}
              type="button"
            >
              {saving ? "正在保存..." : "保存学习状态"}
            </button>
            {success ? <p className="mt-3 text-sm text-[#1d4ed8]">学习状态已更新。</p> : null}
            {saveError ? <p className="mt-3 text-sm text-red-700">{saveError}</p> : null}
          </section>
        </aside>

        <article className="min-w-0 rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60 sm:p-8">
          <p className="text-sm font-semibold text-[#2563eb]">{topic.category}</p>
          <h1 className="mt-3 text-3xl font-semibold leading-tight text-[#0f172a] sm:text-4xl">
            {topic.title}
          </h1>
          <p className="mt-4 leading-7 text-[#475569]">{topic.summary}</p>

          <section className="mt-8 border-t border-[#e2e8f0] pt-6">
            <h2 className="text-xl font-semibold text-[#0f172a]">知识点内容</h2>
            <div className="mt-4 whitespace-pre-wrap break-words rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-5 leading-8 text-[#334155]">
              {topic.content_markdown}
            </div>
          </section>
        </article>
      </div>
    </AppShell>
  );
}
