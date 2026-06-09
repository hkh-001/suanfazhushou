"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

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
      <main className="min-h-screen bg-[#f5f9ff] text-[#0f172a]">
        <section className="mx-auto max-w-4xl px-6 py-12">正在加载知识点详情...</section>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-[#f5f9ff] text-[#0f172a]">
        <section className="mx-auto max-w-4xl px-6 py-12">
          <Link className="text-sm font-semibold text-[#2563eb]" href="/topics">
            返回知识地图
          </Link>
          <p className="mt-6 text-sm font-semibold text-red-700">知识点加载失败</p>
          <p className="mt-2 text-[#475569]">{error ?? "未找到该知识点"}</p>
        </section>
      </main>
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
    <main className="min-h-screen bg-gradient-to-b from-[#eff6ff] via-[#f8fbff] to-white text-[#0f172a]">
      <article className="mx-auto max-w-4xl px-6 py-12">
        <Link className="text-sm font-semibold text-[#2563eb]" href="/topics">
          返回知识地图
        </Link>

        <header className="mt-8 border-b border-[#dbeafe] pb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2563eb]">
            {topic.category}
          </p>
          <h1 className="mt-3 text-4xl font-semibold">{topic.title}</h1>
          <p className="mt-4 leading-7 text-[#475569]">{topic.summary}</p>
          <div className="mt-5 flex flex-wrap gap-3 text-sm text-[#64748b]">
            <span>等级：{topic.level}</span>
            <span>难度：{topic.difficulty_score}/10</span>
            <span>预计用时：{topic.estimated_minutes} 分钟</span>
            <span>学习状态：{statusLabels[topic.learning_status.status]}</span>
          </div>
        </header>

        <section className="mt-8 rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
          <h2 className="text-lg font-semibold">学习状态</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {statusOptions.map((status) => (
              <button
                className={`rounded-md border px-3 py-2 text-sm font-semibold transition ${
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
            className="mt-4 rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white transition hover:bg-[#1d4ed8] disabled:opacity-60"
            disabled={saving}
            onClick={() => void submitStatus()}
            type="button"
          >
            {saving ? "正在保存..." : "保存学习状态"}
          </button>
          {success ? <p className="mt-3 text-sm text-[#1d4ed8]">学习状态已更新。</p> : null}
          {saveError ? <p className="mt-3 text-sm text-red-700">{saveError}</p> : null}
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">知识点内容</h2>
          <div className="mt-4 whitespace-pre-wrap rounded-lg border border-[#dbeafe] bg-white/90 p-6 leading-8 text-[#334155] shadow-sm shadow-blue-100/60">
            {topic.content_markdown}
          </div>
        </section>
      </article>
    </main>
  );
}
