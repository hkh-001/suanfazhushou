import { useState, type ReactNode } from "react";

import type { TopicListItem } from "@/features/topics/types";

export function TopicSelect({
  topics,
  value,
  onChange
}: {
  topics: TopicListItem[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block text-sm font-medium text-[#344250]">
      Topic context
      <select
        className="mt-2 w-full border border-[#c9c1b4] bg-white px-3 py-2"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">No topic context</option>
        {topics.map((topic) => (
          <option key={topic.id} value={topic.id}>
            {topic.title}
          </option>
        ))}
      </select>
    </label>
  );
}

export function ResultPanel({
  title,
  result,
  model,
  promptType,
  inputTokens,
  outputTokens
}: {
  title: string;
  result: string;
  model: string;
  promptType: string;
  inputTokens: number | null;
  outputTokens: number | null;
}) {
  const [copied, setCopied] = useState(false);

  async function copyResult() {
    await navigator.clipboard.writeText(result);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <section className="border border-[#d7d0c3] bg-white/85 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e3dccf] pb-3">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <div className="mt-1 text-xs text-[#50606f]">
            {promptType} · {model} · in {inputTokens ?? "-"} / out {outputTokens ?? "-"}
          </div>
        </div>
        <button
          className="border border-[#c9c1b4] bg-white px-3 py-2 text-xs font-semibold text-[#344250]"
          onClick={() => void copyResult()}
          type="button"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm leading-7 text-[#344250]">
        {result}
      </pre>
    </section>
  );
}

export function FormShell({
  eyebrow,
  title,
  description,
  children
}: {
  eyebrow: string;
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <main className="min-h-screen bg-[#f7f4ee] text-[#1f2933]">
      <section className="mx-auto max-w-5xl px-6 py-12">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#50606f]">{eyebrow}</p>
        <h1 className="mt-3 text-4xl font-semibold">{title}</h1>
        <p className="mt-4 max-w-2xl leading-7 text-[#4a5563]">{description}</p>
        <div className="mt-8">{children}</div>
      </section>
    </main>
  );
}
