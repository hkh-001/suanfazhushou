"use client";

import Link from "next/link";

import { useDashboardSummary } from "./hooks";
import type {
  DashboardActivityItem,
  DashboardCategoryProgress,
  DashboardNextStep,
  DashboardReviewItem,
  DashboardStatusCount
} from "./types";

const statusLabels: Record<string, string> = {
  not_started: "未开始",
  learning: "学习中",
  mastered: "已掌握"
};

const reasonLabels: Record<string, string> = {
  "Learning topic needs another review": "学习中的知识点需要再次复习",
  "Continue reviewing to reach mastery": "继续复习以提升掌握程度",
  "Next published topic with no learning record": "下一个尚未开始的已发布知识点",
  "Continue a topic that is not mastered yet": "继续推进尚未掌握的知识点"
};

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function displayStatus(status: string) {
  return statusLabels[status] ?? status;
}

function displayReason(reason: string) {
  return reasonLabels[reason] ?? reason;
}

function ProgressBar({ value }: { value: number }) {
  const width = `${Math.max(0, Math.min(100, value))}%`;
  return (
    <div className="h-2 w-full rounded-full bg-[#dbeafe]">
      <div className="h-2 rounded-full bg-[#2563eb]" style={{ width }} />
    </div>
  );
}

function StatBlock({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <div className="min-h-28 rounded-lg border border-[#dbeafe] bg-white/90 p-4 shadow-sm shadow-blue-100/60">
      <p className="text-sm text-[#64748b]">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-[#0f172a]">{value}</p>
      {detail ? <p className="mt-2 text-sm text-[#64748b]">{detail}</p> : null}
    </div>
  );
}

function StatusRow({ item }: { item: DashboardStatusCount }) {
  return (
    <div className="grid gap-3 border-b border-[#e2e8f0] py-3 last:border-b-0 sm:grid-cols-[140px_1fr_80px] sm:items-center">
      <div>
        <p className="font-medium">{displayStatus(item.status)}</p>
        <p className="text-sm text-[#64748b]">{item.count} 个知识点</p>
      </div>
      <ProgressBar value={item.percent} />
      <p className="text-sm font-semibold text-[#2563eb] sm:text-right">{item.percent}%</p>
    </div>
  );
}

function CategoryRow({ item }: { item: DashboardCategoryProgress }) {
  return (
    <div className="border-b border-[#e2e8f0] py-4 last:border-b-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{item.category}</h3>
          <p className="mt-1 text-sm text-[#64748b]">
            已开始 {item.started_topics}/{item.total_topics}，已掌握 {item.mastered_topics}
          </p>
        </div>
        <p className="text-sm text-[#64748b]">
          {item.completed_estimated_minutes}/{item.estimated_minutes} 分钟
        </p>
      </div>
      <div className="mt-3">
        <ProgressBar value={item.progress_percent} />
      </div>
    </div>
  );
}

function ActivityRow({ item }: { item: DashboardActivityItem }) {
  return (
    <Link
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] last:border-b-0 hover:text-[#2563eb]"
      href={`/topics/${item.topic_id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{item.title}</p>
          <p className="mt-1 text-sm text-[#64748b]">
            {item.category} / {displayStatus(item.status)} / 掌握度 {item.mastery_level}/5
          </p>
        </div>
        <p className="text-sm text-[#64748b]">{formatDate(item.last_studied_at)}</p>
      </div>
    </Link>
  );
}

function ReviewRow({ item }: { item: DashboardReviewItem }) {
  return (
    <Link
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] last:border-b-0 hover:text-[#2563eb]"
      href={`/topics/${item.topic_id}`}
    >
      <p className="font-semibold">{item.title}</p>
      <p className="mt-1 text-sm text-[#64748b]">
        {displayReason(item.reason)} / 进度 {item.progress_percent}% / 已复习 {item.review_count} 次
      </p>
    </Link>
  );
}

function NextStepRow({ item }: { item: DashboardNextStep }) {
  return (
    <Link
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] last:border-b-0 hover:text-[#2563eb]"
      href={`/topics/${item.topic_id}`}
    >
      <div className="flex gap-3">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#2563eb] text-sm font-semibold text-white">
          {item.rank}
        </span>
        <div>
          <p className="font-semibold">{item.title}</p>
          <p className="mt-1 text-sm text-[#64748b]">
            {item.category} / 难度 {item.difficulty_score}/10 / 预计 {item.estimated_minutes} 分钟
          </p>
          <p className="mt-1 text-sm text-[#64748b]">{displayReason(item.reason)}</p>
        </div>
      </div>
    </Link>
  );
}

export function DashboardPage() {
  const { data, loading, error, reload } = useDashboardSummary();

  if (loading) {
    return (
      <main className="min-h-screen bg-[#f5f9ff] text-[#0f172a]">
        <section className="mx-auto max-w-5xl px-6 py-12">正在加载学习看板...</section>
      </main>
    );
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-[#f5f9ff] px-6 py-12 text-[#0f172a]">
        <section className="mx-auto max-w-3xl rounded-lg border border-[#dbeafe] bg-white/90 p-6 shadow-sm shadow-blue-100/60">
          <h1 className="text-2xl font-semibold">学习看板</h1>
          <p className="mt-4 text-sm font-semibold text-red-700">学习看板加载失败</p>
          <p className="mt-2 text-[#475569]">{error ?? "暂时无法获取学习看板数据。"}</p>
          <button
            className="mt-5 rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white hover:bg-[#1d4ed8]"
            onClick={() => void reload()}
            type="button"
          >
            重试
          </button>
        </section>
      </main>
    );
  }

  const hasLearningRecord = data.recent_activity.length > 0;
  const allMastered = data.total_topics > 0 && data.mastered_topics === data.total_topics;

  return (
    <main className="min-h-screen bg-gradient-to-b from-[#eff6ff] via-[#f8fbff] to-white text-[#0f172a]">
      <section className="mx-auto max-w-6xl px-6 py-12">
        <header className="border-b border-[#dbeafe] pb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2563eb]">
            AlgoMentor AI
          </p>
          <h1 className="mt-3 text-4xl font-semibold">学习看板</h1>
          <p className="mt-4 max-w-3xl leading-7 text-[#475569]">
            查看你的知识点掌握情况、最近学习记录、复习队列和下一步建议。
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white hover:bg-[#1d4ed8]"
              href="/topics"
            >
              知识地图
            </Link>
            <Link
              className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] hover:bg-[#eff6ff]"
              href="/chat"
            >
              AI 问答
            </Link>
            <Link
              className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] hover:bg-[#eff6ff]"
              href="/code-review"
            >
              代码诊断
            </Link>
          </div>
        </header>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatBlock label="知识点总数" value={data.total_topics} />
          <StatBlock label="已开始" value={data.started_topics} />
          <StatBlock label="学习中" value={data.learning_topics} detail={`已掌握 ${data.mastered_topics}`} />
          <StatBlock label="未开始" value={data.not_started_topics} />
          <StatBlock
            label="总体进度"
            value={`${data.progress_percent}%`}
            detail={`已完成 ${data.completed_estimated_minutes}/${data.total_estimated_minutes} 分钟`}
          />
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
          <section className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-xl font-semibold">进度分布</h2>
            <div className="mt-4">
              {data.status_counts.map((item) => (
                <StatusRow item={item} key={item.status} />
              ))}
            </div>
          </section>

          <section className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-xl font-semibold">分类进度</h2>
            <div className="mt-3">
              {data.category_progress.length > 0 ? (
                data.category_progress.map((item) => <CategoryRow item={item} key={item.category} />)
              ) : (
                <p className="py-4 text-sm text-[#64748b]">暂无已发布知识点。</p>
              )}
            </div>
          </section>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <section className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-xl font-semibold">最近学习</h2>
            <div className="mt-3">
              {data.recent_activity.length > 0 ? (
                data.recent_activity.map((item) => <ActivityRow item={item} key={item.topic_id} />)
              ) : (
                <div className="py-4 text-sm text-[#64748b]">
                  <p>暂无学习记录，先从知识地图开始学习吧。</p>
                  <Link className="mt-3 inline-block font-semibold text-[#2563eb]" href="/topics">
                    进入知识地图
                  </Link>
                </div>
              )}
            </div>
          </section>

          <section className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-xl font-semibold">复习队列</h2>
            <div className="mt-3">
              {data.review_queue.length > 0 ? (
                data.review_queue.map((item) => <ReviewRow item={item} key={item.topic_id} />)
              ) : (
                <p className="py-4 text-sm text-[#64748b]">
                  {hasLearningRecord ? "当前没有需要复习的知识点。" : "暂无复习项目。"}
                </p>
              )}
            </div>
          </section>

          <section className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="text-xl font-semibold">下一步建议</h2>
            <div className="mt-3">
              {data.next_steps.length > 0 ? (
                data.next_steps.map((item) => <NextStepRow item={item} key={item.topic_id} />)
              ) : (
                <p className="py-4 text-sm text-[#64748b]">
                  {allMastered
                    ? "恭喜，你已完成当前所有知识点。"
                    : "暂无下一步建议，请先从知识地图开始学习。"}
                </p>
              )}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
