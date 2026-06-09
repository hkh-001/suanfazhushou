"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { useTopic, useUpdateLearningRecord } from "./hooks";
import type { LearningRecordPayload } from "./types";

const statusOptions: LearningRecordPayload["status"][] = ["not_started", "learning", "mastered"];

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
    return <main className="mx-auto max-w-4xl px-6 py-12">Loading topic detail...</main>;
  }

  if (error || !data) {
    return (
      <main className="mx-auto max-w-4xl px-6 py-12">
        <Link className="text-sm text-[#2f6f73]" href="/topics">
          Back to knowledge map
        </Link>
        <p className="mt-6 text-sm font-semibold text-red-700">Failed to load</p>
        <p className="mt-2 text-[#4a5563]">{error ?? "Topic not found"}</p>
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
    <main className="min-h-screen bg-[#f7f4ee] text-[#1f2933]">
      <article className="mx-auto max-w-4xl px-6 py-12">
        <Link className="text-sm text-[#2f6f73]" href="/topics">
          Back to knowledge map
        </Link>

        <header className="mt-8 border-b border-[#d7d0c3] pb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#50606f]">
            {topic.category}
          </p>
          <h1 className="mt-3 text-4xl font-semibold">{topic.title}</h1>
          <p className="mt-4 leading-7 text-[#4a5563]">{topic.summary}</p>
          <div className="mt-5 flex flex-wrap gap-3 text-sm text-[#50606f]">
            <span>Level: {topic.level}</span>
            <span>Difficulty: {topic.difficulty_score}/10</span>
            <span>{topic.estimated_minutes} min</span>
            <span>Status: {topic.learning_status.status}</span>
          </div>
        </header>

        <section className="mt-8 border border-[#d7d0c3] bg-white/80 p-5">
          <h2 className="text-lg font-semibold">Learning status</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {statusOptions.map((status) => (
              <button
                className={`border px-3 py-2 text-sm ${
                  selectedStatus === status
                    ? "border-[#2f6f73] bg-[#2f6f73] text-white"
                    : "border-[#c9c1b4] bg-white text-[#1f2933]"
                }`}
                key={status}
                onClick={() => setSelectedStatus(status)}
                type="button"
              >
                {status}
              </button>
            ))}
          </div>
          <button
            className="mt-4 bg-[#1f2933] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            disabled={saving}
            onClick={() => void submitStatus()}
            type="button"
          >
            {saving ? "Saving..." : "Save learning status"}
          </button>
          {success ? <p className="mt-3 text-sm text-[#2f6f73]">Learning status updated.</p> : null}
          {saveError ? <p className="mt-3 text-sm text-red-700">{saveError}</p> : null}
        </section>

        <section className="mt-8">
          <h2 className="text-xl font-semibold">Topic content</h2>
          <div className="mt-4 whitespace-pre-wrap border border-[#d7d0c3] bg-white/80 p-6 leading-8 text-[#344250]">
            {topic.content_markdown}
          </div>
        </section>
      </article>
    </main>
  );
}
