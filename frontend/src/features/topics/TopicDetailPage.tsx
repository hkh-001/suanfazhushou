"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MarkdownContent } from "@/components/MarkdownContent";

import { useInteractiveLesson, useTopic, useUpdateLearningRecord } from "./hooks";
import type { InteractiveLesson, LearningRecordPayload } from "./types";

const statusOptions: LearningRecordPayload["status"][] = ["not_started", "learning", "mastered"];
const statusLabels: Record<LearningRecordPayload["status"], string> = {
  not_started: "未开始",
  learning: "学习中",
  mastered: "已掌握"
};

const lessonStatusLabels: Record<InteractiveLesson["status"], string> = {
  pending: "等待提交",
  submitted: "已提交",
  processing: "生成中",
  completed: "已完成",
  failed: "生成失败"
};

const pollableLessonStatuses = new Set<InteractiveLesson["status"]>(["pending", "submitted", "processing"]);
const POLL_INTERVAL_MS = 5000;
const MAX_POLL_MS = 5 * 60 * 1000;

function InteractiveLessonCard({
  topicId,
  lesson,
  loading,
  error,
  onGenerate,
  onRefresh
}: {
  topicId: string;
  lesson: InteractiveLesson | null;
  loading: boolean;
  error: string | null;
  onGenerate: (topicId: string, force?: boolean) => Promise<InteractiveLesson | null>;
  onRefresh: (lessonId: string) => Promise<InteractiveLesson | null>;
}) {
  const [manualRefreshing, setManualRefreshing] = useState(false);
  const lessonId = lesson?.id;
  const lessonStatus = lesson?.status;

  useEffect(() => {
    if (!lessonId || !lessonStatus || !pollableLessonStatuses.has(lessonStatus)) {
      return;
    }
    let cancelled = false;
    const startedAt = Date.now();
    const intervalId = window.setInterval(() => {
      if (cancelled || Date.now() - startedAt > MAX_POLL_MS) {
        window.clearInterval(intervalId);
        return;
      }
      void onRefresh(lessonId);
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [lessonId, lessonStatus, onRefresh]);

  async function handleRefresh() {
    if (!lesson) {
      return;
    }
    setManualRefreshing(true);
    try {
      await onRefresh(lesson.id);
    } finally {
      setManualRefreshing(false);
    }
  }

  return (
    <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-[#0f172a]">互动课堂</h2>
          <p className="mt-2 text-sm leading-6 text-[#64748b]">
            由 OpenMAIC 外部服务生成互动式课堂。生成过程不会修改你的学习状态，也不会发送学号、代码或私有记录。
          </p>
        </div>
        {lesson ? (
          <span className="inline-flex w-fit rounded-full border border-[#bfdbfe] bg-[#eff6ff] px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
            {lessonStatusLabels[lesson.status]}
          </span>
        ) : null}
      </div>

      {lesson ? (
        <div className="mt-4 rounded-lg border border-[#e2e8f0] bg-[#f8fbff] p-4 text-sm text-[#334155]">
          <p className="font-semibold text-[#0f172a]">{lesson.title}</p>
          <p className="mt-2">状态：{lessonStatusLabels[lesson.status]}</p>
          {lesson.error_message ? <p className="mt-2 text-red-700">{lesson.error_message}</p> : null}
          {lesson.status === "completed" && lesson.classroom_url ? (
            <a
              className="mt-4 inline-flex rounded-md bg-[#2563eb] px-4 py-2 font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href={lesson.classroom_url}
              rel="noopener noreferrer"
              target="_blank"
            >
              打开互动课堂
            </a>
          ) : null}
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-3">
        {!lesson || lesson.status === "failed" ? (
          <button
            className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
            disabled={loading}
            onClick={() => void onGenerate(topicId, lesson?.status === "failed")}
            type="button"
          >
            {loading ? "正在提交..." : lesson?.status === "failed" ? "重新生成" : "生成互动课堂"}
          </button>
        ) : null}
        {lesson?.status === "completed" ? (
          <button
            className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
            disabled={loading}
            onClick={() => void onGenerate(topicId, true)}
            type="button"
          >
            重新生成课堂
          </button>
        ) : null}
        {lesson && pollableLessonStatuses.has(lesson.status) ? (
          <button
            className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
            disabled={manualRefreshing}
            onClick={() => void handleRefresh()}
            type="button"
          >
            {manualRefreshing ? "正在刷新..." : "刷新状态"}
          </button>
        ) : null}
      </div>

      {error ? <p className="mt-3 text-sm text-red-700">{error}</p> : null}
    </section>
  );
}

export function TopicDetailPage({ id }: { id: string }) {
  const { data, loading, error, reload } = useTopic(id);
  const { update, loading: saving, error: saveError, success } = useUpdateLearningRecord();
  const { lesson, loading: lessonLoading, error: lessonError, generate, refresh } = useInteractiveLesson();
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
                <dd className="mt-1 font-semibold text-[#0f172a]">{statusLabels[topic.learning_status.status]}</dd>
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

          <InteractiveLessonCard
            error={lessonError}
            lesson={lesson}
            loading={lessonLoading}
            onGenerate={generate}
            onRefresh={refresh}
            topicId={topic.id}
          />
        </aside>

        <article className="min-w-0 rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60 sm:p-8">
          <p className="text-sm font-semibold text-[#2563eb]">{topic.category}</p>
          <h1 className="mt-3 text-3xl font-semibold leading-tight text-[#0f172a] sm:text-4xl">{topic.title}</h1>
          <p className="mt-4 leading-7 text-[#475569]">{topic.summary}</p>

          <section className="mt-8 border-t border-[#e2e8f0] pt-6">
            <h2 className="text-xl font-semibold text-[#0f172a]">知识点内容</h2>
            <div className="mt-4 rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-5">
              <MarkdownContent content={topic.content_markdown} />
            </div>
          </section>
        </article>
      </div>
    </AppShell>
  );
}
