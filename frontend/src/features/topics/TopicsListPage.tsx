"use client";

import Link from "next/link";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useTopics } from "./hooks";
import type { TopicListItem } from "./types";

const statusLabels: Record<TopicListItem["learning_status"]["status"], string> = {
  not_started: "未开始",
  learning: "学习中",
  mastered: "已掌握"
};

function groupByCategory(topics: TopicListItem[]) {
  return topics.reduce<Record<string, TopicListItem[]>>((groups, topic) => {
    groups[topic.category] ??= [];
    groups[topic.category].push(topic);
    return groups;
  }, {});
}

function TopicCard({ topic }: { topic: TopicListItem }) {
  return (
    <Link
      className="block rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60 outline-none transition hover:-translate-y-0.5 hover:border-[#93c5fd] hover:shadow-md focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
      href={`/topics/${topic.id}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold text-[#0f172a]">{topic.title}</h3>
          <p className="mt-2 text-sm leading-6 text-[#475569]">{topic.summary}</p>
        </div>
        <span className="whitespace-nowrap rounded-md border border-[#bfdbfe] bg-[#eff6ff] px-2.5 py-1 text-xs font-semibold text-[#1d4ed8]">
          {statusLabels[topic.learning_status.status]}
        </span>
      </div>
      <div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-[#64748b]">
        <span>阶段：{topic.level}</span>
        <span>难度：{topic.difficulty_score}/10</span>
        <span>预计用时：{topic.estimated_minutes} 分钟</span>
      </div>
      <span className="mt-4 inline-flex text-sm font-semibold text-[#2563eb]">查看详情</span>
    </Link>
  );
}

export function TopicsListPage() {
  const { data, loading, error } = useTopics();
  const groups = data ? groupByCategory(data.data) : {};

  return (
    <AppShell>
      <PageHeader
        description="按照算法基础路线系统学习核心知识点，查看当前学习状态，并进入详情页更新掌握进度。"
        title="知识地图"
      />

      {loading ? (
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
          正在加载知识地图...
        </section>
      ) : null}

      {error ? (
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">知识地图加载失败</p>
          <p className="mt-2 text-sm">{error}</p>
          {error === "请先登录后继续使用。" ? (
            <Link
              className="mt-4 inline-flex font-semibold text-[#1d4ed8] underline-offset-4 hover:underline"
              href="/login"
            >
              去登录
            </Link>
          ) : null}
        </section>
      ) : null}

      {!loading && !error && (!data || data.data.length === 0) ? (
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
          暂无已发布知识点。
        </section>
      ) : null}

      {!loading && !error && data && data.data.length > 0 ? (
        <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
          <aside className="space-y-4">
            <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
              <h2 className="text-lg font-semibold text-[#0f172a]">学习路线</h2>
              <p className="mt-2 text-sm leading-6 text-[#64748b]">
                先建立基础概念，再进入模板、技巧和综合应用。当前页面先按分类平铺展示，不增加复杂筛选。
              </p>
            </section>

            <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
              <h2 className="text-lg font-semibold text-[#0f172a]">分类摘要</h2>
              <div className="mt-3 space-y-2 text-sm text-[#475569]">
                {Object.entries(groups).map(([category, topics]) => (
                  <div className="flex items-center justify-between gap-3" key={category}>
                    <span>{category}</span>
                    <span className="rounded-full bg-[#eff6ff] px-2 py-0.5 text-xs font-semibold text-[#1d4ed8]">
                      {topics.length} 个
                    </span>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
              <h2 className="text-lg font-semibold text-[#0f172a]">状态说明</h2>
              <div className="mt-3 space-y-2 text-sm text-[#475569]">
                <p>未开始：还没有学习记录。</p>
                <p>学习中：已开始，需要继续复习。</p>
                <p>已掌握：当前知识点已完成。</p>
              </div>
            </section>
          </aside>

          <section className="space-y-8">
            {Object.entries(groups).map(([category, topics]) => (
              <section key={category}>
                <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-semibold text-[#0f172a]">{category}</h2>
                    <p className="mt-1 text-sm text-[#64748b]">共 {topics.length} 个知识点</p>
                  </div>
                </div>
                <div className="grid gap-4 xl:grid-cols-2">
                  {topics.map((topic) => (
                    <TopicCard key={topic.id} topic={topic} />
                  ))}
                </div>
              </section>
            ))}
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
