"use client";

import Link from "next/link";

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

export function TopicsListPage() {
  const { data, loading, error } = useTopics();

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f5f9ff] text-[#0f172a]">
        <section className="mx-auto max-w-6xl px-6 py-12">正在加载知识地图...</section>
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen bg-[#f5f9ff] text-[#0f172a]">
        <section className="mx-auto max-w-6xl px-6 py-12">
          <p className="text-sm font-semibold text-red-700">知识地图加载失败</p>
          <p className="mt-2 text-[#475569]">{error}</p>
        </section>
      </main>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <main className="min-h-screen bg-[#f5f9ff] text-[#0f172a]">
        <section className="mx-auto max-w-6xl px-6 py-12">暂无已发布知识点。</section>
      </main>
    );
  }

  const groups = groupByCategory(data.data);

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#eff6ff] via-[#f8fbff] to-white text-[#0f172a]">
      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2563eb]">
            AlgoMentor AI
          </p>
          <h1 className="mt-3 text-4xl font-semibold">知识地图</h1>
          <p className="mt-4 max-w-2xl leading-7 text-[#475569]">
            系统学习算法基础知识点，查看当前学习状态，并进入详情页更新掌握进度。
          </p>
        </div>

        <div className="space-y-10">
          {Object.entries(groups).map(([category, topics]) => (
            <section key={category}>
              <h2 className="mb-4 text-xl font-semibold">{category}</h2>
              <div className="grid gap-4 md:grid-cols-2">
                {topics.map((topic) => (
                  <Link
                    className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60 transition hover:-translate-y-0.5 hover:border-[#93c5fd] hover:shadow-md"
                    href={`/topics/${topic.id}`}
                    key={topic.id}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-semibold">{topic.title}</h3>
                        <p className="mt-2 text-sm leading-6 text-[#475569]">{topic.summary}</p>
                      </div>
                      <span className="whitespace-nowrap rounded-md border border-[#bfdbfe] bg-[#eff6ff] px-2 py-1 text-xs font-semibold text-[#1d4ed8]">
                        {statusLabels[topic.learning_status.status]}
                      </span>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-[#64748b]">
                      <span>等级：{topic.level}</span>
                      <span>难度：{topic.difficulty_score}/10</span>
                      <span>预计用时：{topic.estimated_minutes} 分钟</span>
                    </div>
                    <span className="mt-4 inline-flex text-sm font-semibold text-[#2563eb]">查看详情</span>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>
    </main>
  );
}
