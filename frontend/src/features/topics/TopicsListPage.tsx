"use client";

import Link from "next/link";

import { useTopics } from "./hooks";
import type { TopicListItem } from "./types";

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
    return <main className="mx-auto max-w-6xl px-6 py-12">Loading topics...</main>;
  }

  if (error) {
    return (
      <main className="mx-auto max-w-6xl px-6 py-12">
        <p className="text-sm font-semibold text-red-700">Failed to load topics</p>
        <p className="mt-2 text-[#4a5563]">{error}</p>
      </main>
    );
  }

  if (!data || data.data.length === 0) {
    return <main className="mx-auto max-w-6xl px-6 py-12">No published topics yet.</main>;
  }

  const groups = groupByCategory(data.data);

  return (
    <main className="min-h-screen bg-[#f7f4ee] text-[#1f2933]">
      <section className="mx-auto max-w-6xl px-6 py-12">
        <div className="mb-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#50606f]">
            Knowledge Map
          </p>
          <h1 className="mt-3 text-4xl font-semibold">Algorithm knowledge map</h1>
          <p className="mt-4 max-w-2xl leading-7 text-[#4a5563]">
            Phase 2 shows published foundational topics and the current learning status.
          </p>
        </div>

        <div className="space-y-10">
          {Object.entries(groups).map(([category, topics]) => (
            <section key={category}>
              <h2 className="mb-4 text-xl font-semibold">{category}</h2>
              <div className="grid gap-4 md:grid-cols-2">
                {topics.map((topic) => (
                  <Link
                    className="border border-[#d7d0c3] bg-white/80 p-5 shadow-sm transition hover:border-[#2f6f73]"
                    href={`/topics/${topic.id}`}
                    key={topic.id}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-semibold">{topic.title}</h3>
                        <p className="mt-2 text-sm leading-6 text-[#4a5563]">{topic.summary}</p>
                      </div>
                      <span className="whitespace-nowrap border border-[#c9c1b4] px-2 py-1 text-xs">
                        {topic.learning_status.status}
                      </span>
                    </div>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-[#50606f]">
                      <span>Level: {topic.level}</span>
                      <span>Difficulty: {topic.difficulty_score}/10</span>
                      <span>{topic.estimated_minutes} min</span>
                    </div>
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
