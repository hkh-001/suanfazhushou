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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function ProgressBar({ value }: { value: number }) {
  const width = `${Math.max(0, Math.min(100, value))}%`;
  return (
    <div className="h-2 w-full bg-[#e5ded1]">
      <div className="h-2 bg-[#2f6f73]" style={{ width }} />
    </div>
  );
}

function StatBlock({ label, value, detail }: { label: string; value: string | number; detail?: string }) {
  return (
    <div className="min-h-28 border border-[#d7d0c3] bg-white/80 p-4">
      <p className="text-sm text-[#50606f]">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-[#1f2933]">{value}</p>
      {detail ? <p className="mt-2 text-sm text-[#64717f]">{detail}</p> : null}
    </div>
  );
}

function StatusRow({ item }: { item: DashboardStatusCount }) {
  return (
    <div className="grid gap-3 border-b border-[#e1dacd] py-3 last:border-b-0 sm:grid-cols-[140px_1fr_80px] sm:items-center">
      <div>
        <p className="font-medium">{item.label}</p>
        <p className="text-sm text-[#64717f]">{item.count} topics</p>
      </div>
      <ProgressBar value={item.percent} />
      <p className="text-sm font-semibold text-[#2f6f73] sm:text-right">{item.percent}%</p>
    </div>
  );
}

function CategoryRow({ item }: { item: DashboardCategoryProgress }) {
  return (
    <div className="border-b border-[#e1dacd] py-4 last:border-b-0">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{item.category}</h3>
          <p className="mt-1 text-sm text-[#64717f]">
            {item.started_topics}/{item.total_topics} started, {item.mastered_topics} mastered
          </p>
        </div>
        <p className="text-sm text-[#50606f]">
          {item.completed_estimated_minutes}/{item.estimated_minutes} min
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
      className="block border-b border-[#e1dacd] py-4 text-[#1f2933] last:border-b-0 hover:text-[#2f6f73]"
      href={`/topics/${item.topic_id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-semibold">{item.title}</p>
          <p className="mt-1 text-sm text-[#64717f]">
            {item.category} · {item.status} · mastery {item.mastery_level}/5
          </p>
        </div>
        <p className="text-sm text-[#50606f]">{formatDate(item.last_studied_at)}</p>
      </div>
    </Link>
  );
}

function ReviewRow({ item }: { item: DashboardReviewItem }) {
  return (
    <Link
      className="block border-b border-[#e1dacd] py-4 text-[#1f2933] last:border-b-0 hover:text-[#2f6f73]"
      href={`/topics/${item.topic_id}`}
    >
      <p className="font-semibold">{item.title}</p>
      <p className="mt-1 text-sm text-[#64717f]">
        {item.reason} · progress {item.progress_percent}% · reviewed {item.review_count} times
      </p>
    </Link>
  );
}

function NextStepRow({ item }: { item: DashboardNextStep }) {
  return (
    <Link
      className="block border-b border-[#e1dacd] py-4 text-[#1f2933] last:border-b-0 hover:text-[#2f6f73]"
      href={`/topics/${item.topic_id}`}
    >
      <div className="flex gap-3">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center bg-[#1f2933] text-sm font-semibold text-white">
          {item.rank}
        </span>
        <div>
          <p className="font-semibold">{item.title}</p>
          <p className="mt-1 text-sm text-[#64717f]">
            {item.category} · difficulty {item.difficulty_score}/10 · {item.estimated_minutes} min
          </p>
          <p className="mt-1 text-sm text-[#50606f]">{item.reason}</p>
        </div>
      </div>
    </Link>
  );
}

export function DashboardPage() {
  const { data, loading, error, reload } = useDashboardSummary();

  if (loading) {
    return <main className="mx-auto max-w-5xl px-6 py-12">Loading dashboard...</main>;
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-[#f7f4ee] px-6 py-12 text-[#1f2933]">
        <section className="mx-auto max-w-3xl border border-[#d7d0c3] bg-white/80 p-6">
          <h1 className="text-2xl font-semibold">Learning Dashboard</h1>
          <p className="mt-4 text-sm font-semibold text-red-700">Failed to load dashboard</p>
          <p className="mt-2 text-[#4a5563]">{error ?? "Dashboard data is unavailable."}</p>
          <button
            className="mt-5 bg-[#1f2933] px-4 py-2 text-sm font-semibold text-white"
            onClick={() => void reload()}
            type="button"
          >
            Retry
          </button>
        </section>
      </main>
    );
  }

  const hasLearningRecord = data.recent_activity.length > 0;
  const allMastered = data.total_topics > 0 && data.mastered_topics === data.total_topics;

  return (
    <main className="min-h-screen bg-[#f7f4ee] text-[#1f2933]">
      <section className="mx-auto max-w-6xl px-6 py-12">
        <header className="border-b border-[#d7d0c3] pb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#50606f]">
            AlgoMentor AI
          </p>
          <h1 className="mt-3 text-4xl font-semibold">Learning Dashboard</h1>
          <p className="mt-4 max-w-3xl leading-7 text-[#4a5563]">
            Track your topic progress, recent study activity, review queue, and the next
            rule-based step in the learning loop.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link className="bg-[#1f2933] px-4 py-2 text-sm font-semibold text-white" href="/topics">
              Knowledge map
            </Link>
            <Link className="border border-[#9aa6b2] px-4 py-2 text-sm font-semibold" href="/chat">
              AI tutor
            </Link>
            <Link className="border border-[#9aa6b2] px-4 py-2 text-sm font-semibold" href="/code-review">
              Code review
            </Link>
          </div>
        </header>

        <section className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatBlock label="Total topics" value={data.total_topics} />
          <StatBlock label="Started" value={data.started_topics} />
          <StatBlock label="Learning" value={data.learning_topics} detail={`${data.mastered_topics} mastered`} />
          <StatBlock label="Not started" value={data.not_started_topics} />
          <StatBlock
            label="Overall progress"
            value={`${data.progress_percent}%`}
            detail={`${data.completed_estimated_minutes}/${data.total_estimated_minutes} min completed`}
          />
        </section>

        <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_1fr]">
          <section className="border border-[#d7d0c3] bg-white/80 p-5">
            <h2 className="text-xl font-semibold">Progress distribution</h2>
            <div className="mt-4">
              {data.status_counts.map((item) => (
                <StatusRow item={item} key={item.status} />
              ))}
            </div>
          </section>

          <section className="border border-[#d7d0c3] bg-white/80 p-5">
            <h2 className="text-xl font-semibold">Category progress</h2>
            <div className="mt-3">
              {data.category_progress.length > 0 ? (
                data.category_progress.map((item) => <CategoryRow item={item} key={item.category} />)
              ) : (
                <p className="py-4 text-sm text-[#64717f]">No published topics are available.</p>
              )}
            </div>
          </section>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-3">
          <section className="border border-[#d7d0c3] bg-white/80 p-5">
            <h2 className="text-xl font-semibold">Recent activity</h2>
            <div className="mt-3">
              {data.recent_activity.length > 0 ? (
                data.recent_activity.map((item) => <ActivityRow item={item} key={item.topic_id} />)
              ) : (
                <div className="py-4 text-sm text-[#64717f]">
                  <p>Start learning from the knowledge map.</p>
                  <Link className="mt-3 inline-block font-semibold text-[#2f6f73]" href="/topics">
                    Open knowledge map
                  </Link>
                </div>
              )}
            </div>
          </section>

          <section className="border border-[#d7d0c3] bg-white/80 p-5">
            <h2 className="text-xl font-semibold">Review queue</h2>
            <div className="mt-3">
              {data.review_queue.length > 0 ? (
                data.review_queue.map((item) => <ReviewRow item={item} key={item.topic_id} />)
              ) : (
                <p className="py-4 text-sm text-[#64717f]">
                  {hasLearningRecord ? "All started topics are up to date." : "No review items yet."}
                </p>
              )}
            </div>
          </section>

          <section className="border border-[#d7d0c3] bg-white/80 p-5">
            <h2 className="text-xl font-semibold">Next steps</h2>
            <div className="mt-3">
              {data.next_steps.length > 0 ? (
                data.next_steps.map((item) => <NextStepRow item={item} key={item.topic_id} />)
              ) : (
                <p className="py-4 text-sm text-[#64717f]">
                  {allMastered
                    ? "Congratulations! You've completed all topics."
                    : "Start learning from the knowledge map."}
                </p>
              )}
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
