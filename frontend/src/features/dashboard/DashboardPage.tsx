"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useDashboardSummary } from "./hooks";
import type {
  DashboardActivityItem,
  DashboardCategoryProgress,
  DashboardNextStep,
  DashboardPracticeRecommendation,
  DashboardRecommendationAction,
  DashboardReviewItem,
  DashboardStatusCount,
  DashboardWeakTopic
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

const difficultyLabels: Record<string, string> = {
  beginner: "入门",
  basic: "基础",
  intermediate: "提高",
  advanced: "进阶"
};

const actionTypeLabels: Record<string, string> = {
  review_topic: "复习知识点",
  review_mistake: "处理复盘",
  retry_problem: "重做题目",
  practice_problem: "练习巩固"
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
    <div className="min-h-28 rounded-xl border border-[#dbeafe] bg-white/95 p-4 shadow-sm shadow-blue-100/60">
      <p className="text-sm text-[#64748b]">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-[#0f172a]">{value}</p>
      {detail ? <p className="mt-2 text-sm text-[#64748b]">{detail}</p> : null}
    </div>
  );
}

function StatusRow({ item }: { item: DashboardStatusCount }) {
  return (
    <div className="grid gap-3 border-b border-[#e2e8f0] py-3 last:border-b-0 sm:grid-cols-[120px_1fr_72px] sm:items-center">
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
          <h3 className="font-semibold text-[#0f172a]">{item.category}</h3>
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
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] outline-none last:border-b-0 hover:text-[#2563eb] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
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
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] outline-none last:border-b-0 hover:text-[#2563eb] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
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
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] outline-none last:border-b-0 hover:text-[#2563eb] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
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

function targetHref(targetType: DashboardRecommendationAction["target_type"], targetId: string) {
  if (targetType === "topic") {
    return `/topics/${targetId}`;
  }
  if (targetType === "mistake") {
    return `/mistakes/${targetId}`;
  }
  if (targetType === "problem") {
    return `/problems/${targetId}`;
  }
  return `/submissions/${targetId}`;
}

function WeakTopicRow({ item }: { item: DashboardWeakTopic }) {
  return (
    <Link
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] outline-none last:border-b-0 hover:text-[#2563eb] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
      href={`/topics/${item.topic_id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{item.title}</p>
          <p className="mt-1 text-sm text-[#64748b]">{item.category}</p>
        </div>
        <span className="rounded-full bg-[#eff6ff] px-3 py-1 text-sm font-semibold text-[#1d4ed8]">
          {item.weakness_score}
        </span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {item.signals.map((signal) => (
          <span className="rounded-full border border-[#bfdbfe] bg-white px-2.5 py-1 text-xs text-[#1d4ed8]" key={signal}>
            {signal}
          </span>
        ))}
      </div>
      <p className="mt-3 text-sm text-[#475569]">{item.reason}</p>
      <p className="mt-1 text-sm font-medium text-[#2563eb]">{item.recommended_action}</p>
    </Link>
  );
}

function RecommendationActionRow({ item }: { item: DashboardRecommendationAction }) {
  return (
    <Link
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] outline-none last:border-b-0 hover:text-[#2563eb] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
      href={targetHref(item.target_type, item.target_id)}
    >
      <div className="flex gap-3">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#dbeafe] text-sm font-semibold text-[#1d4ed8]">
          P{item.priority}
        </span>
        <div>
          <p className="text-sm font-medium text-[#2563eb]">{actionTypeLabels[item.type] ?? item.type}</p>
          <p className="mt-1 font-semibold">{item.title}</p>
          <p className="mt-1 text-sm text-[#64748b]">{item.reason}</p>
        </div>
      </div>
    </Link>
  );
}

function PracticeRecommendationRow({ item }: { item: DashboardPracticeRecommendation }) {
  return (
    <Link
      className="block border-b border-[#e2e8f0] py-4 text-[#0f172a] outline-none last:border-b-0 hover:text-[#2563eb] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
      href={`/problems/${item.problem_id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">
            #{item.display_id} {item.title}
          </p>
          <p className="mt-1 text-sm text-[#64748b]">{difficultyLabels[item.difficulty] ?? item.difficulty}</p>
        </div>
        <span className="rounded-full bg-[#eff6ff] px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
          优先级 {item.priority}
        </span>
      </div>
      {item.topic_tags.length > 0 ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {item.topic_tags.map((tag) => (
            <span className="rounded-full border border-[#bfdbfe] bg-white px-2.5 py-1 text-xs text-[#1d4ed8]" key={tag.id}>
              {tag.title}
            </span>
          ))}
        </div>
      ) : null}
      <p className="mt-3 text-sm text-[#64748b]">{item.reason}</p>
    </Link>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
      <h2 className="text-xl font-semibold text-[#0f172a]">{title}</h2>
      <div className="mt-3">{children}</div>
    </section>
  );
}

export function DashboardPage() {
  const { data, loading, error, reload } = useDashboardSummary();

  if (loading) {
    return (
      <AppShell>
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
          正在加载学习看板...
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell maxWidth="max-w-6xl">
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 shadow-sm shadow-blue-100/60">
          <h1 className="text-2xl font-semibold text-[#0f172a]">学习看板</h1>
          <p className="mt-4 text-sm font-semibold text-red-700">学习看板加载失败</p>
          <p className="mt-2 text-[#475569]">{error ?? "暂时无法获取学习看板数据。"}</p>
          <div className="mt-5 flex flex-wrap gap-3">
            {error === "请先登录后继续使用。" ? (
              <Link
                className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                href="/login"
              >
                去登录
              </Link>
            ) : null}
            <button
              className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              onClick={() => void reload()}
              type="button"
            >
              重试
            </button>
          </div>
        </section>
      </AppShell>
    );
  }

  const hasLearningRecord = data.recent_activity.length > 0;
  const allMastered = data.total_topics > 0 && data.mastered_topics === data.total_topics;

  return (
    <AppShell>
      <PageHeader
        actions={
          <>
            <Link
              className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href="/topics"
            >
              知识地图
            </Link>
            <Link
              className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href="/chat"
            >
              AI 问答
            </Link>
          </>
        }
        description="查看你的知识点掌握情况、最近学习记录、复习队列和下一步建议。"
        title="学习看板"
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
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

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Panel title="进度分布">
          {data.status_counts.map((item) => (
            <StatusRow item={item} key={item.status} />
          ))}
        </Panel>

        <Panel title="分类进度">
          {data.category_progress.length > 0 ? (
            data.category_progress.map((item) => <CategoryRow item={item} key={item.category} />)
          ) : (
            <p className="py-4 text-sm text-[#64748b]">暂无已发布知识点。</p>
          )}
        </Panel>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Panel title="薄弱点分析">
          {data.weak_topics.length > 0 ? (
            data.weak_topics.map((item) => <WeakTopicRow item={item} key={item.topic_id} />)
          ) : (
            <p className="py-4 text-sm text-[#64748b]">暂无明确薄弱点，继续学习或提交练习后会生成建议。</p>
          )}
        </Panel>

        <Panel title="推荐行动">
          {data.recommendation_actions.length > 0 ? (
            data.recommendation_actions.map((item) => (
              <RecommendationActionRow item={item} key={`${item.target_type}-${item.target_id}-${item.type}`} />
            ))
          ) : (
            <p className="py-4 text-sm text-[#64748b]">暂无需要优先处理的复盘或失败提交。</p>
          )}
        </Panel>

        <Panel title="推荐练习">
          {data.practice_recommendations.length > 0 ? (
            data.practice_recommendations.map((item) => <PracticeRecommendationRow item={item} key={item.problem_id} />)
          ) : (
            <p className="py-4 text-sm text-[#64748b]">暂无匹配的个人题库练习。</p>
          )}
        </Panel>
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        <Panel title="最近学习">
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
        </Panel>

        <Panel title="复习队列">
          {data.review_queue.length > 0 ? (
            data.review_queue.map((item) => <ReviewRow item={item} key={item.topic_id} />)
          ) : (
            <p className="py-4 text-sm text-[#64748b]">
              {hasLearningRecord ? "当前没有需要复习的知识点。" : "暂无复习项目。"}
            </p>
          )}
        </Panel>

        <Panel title="下一步建议">
          {data.next_steps.length > 0 ? (
            data.next_steps.map((item) => <NextStepRow item={item} key={item.topic_id} />)
          ) : (
            <p className="py-4 text-sm text-[#64748b]">
              {allMastered ? "恭喜，你已完成当前所有知识点。" : "暂无下一步建议，请先从知识地图开始学习。"}
            </p>
          )}
        </Panel>
      </div>
    </AppShell>
  );
}
