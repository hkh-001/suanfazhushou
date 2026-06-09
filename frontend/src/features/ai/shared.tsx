import { useState, type ReactNode } from "react";
import Link from "next/link";

import type { TopicListItem } from "@/features/topics/types";

export function friendlyAIError(error: unknown) {
  const message = error instanceof Error ? error.message : "";
  if (message.includes("AI provider configuration is missing")) {
    return "当前未配置 AI 服务，请先进入“系统设置”配置接口地址、API 密钥和模型名称。";
  }
  if (message.includes("AI provider request timed out")) {
    return "AI 服务响应超时，请稍后重试。";
  }
  if (message.includes("AI provider returned an error")) {
    return "AI 服务暂时返回错误，请稍后重试。";
  }
  if (message.includes("AI output could not be parsed")) {
    return "AI 返回内容暂时无法解析，请调整输入后重试。";
  }
  return message || "请求失败，请稍后重试。";
}

export function AIErrorNotice({ message }: { message: string }) {
  const showSettingsLink = message.includes("未配置 AI 服务");
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-700">
      <p>{message}</p>
      {showSettingsLink ? (
        <Link className="mt-3 inline-flex text-[#1d4ed8] underline-offset-4 hover:underline" href="/settings">
          去配置 AI 服务
        </Link>
      ) : null}
    </div>
  );
}

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
    <label className="block text-sm font-medium text-[#334155]">
      选择知识点
      <select
        className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
        onChange={(event) => onChange(event.target.value)}
        value={value}
      >
        <option value="">不使用知识点上下文</option>
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
    <section className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e2e8f0] pb-3">
        <div>
          <h2 className="text-lg font-semibold">{title}</h2>
          <div className="mt-1 text-xs text-[#64748b]">
            模板：{promptType} / 模型：{model} / 输入 token：{inputTokens ?? "-"} / 输出 token：
            {outputTokens ?? "-"}
          </div>
        </div>
        <button
          className="rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-xs font-semibold text-[#1d4ed8] hover:bg-[#eff6ff]"
          onClick={() => void copyResult()}
          type="button"
        >
          {copied ? "已复制" : "复制"}
        </button>
      </div>
      <pre className="mt-4 whitespace-pre-wrap break-words font-sans text-sm leading-7 text-[#334155]">
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
    <main className="min-h-screen bg-gradient-to-b from-[#eff6ff] via-[#f8fbff] to-white text-[#0f172a]">
      <section className="mx-auto max-w-5xl px-6 py-12">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2563eb]">{eyebrow}</p>
        <h1 className="mt-3 text-4xl font-semibold">{title}</h1>
        <p className="mt-4 max-w-2xl leading-7 text-[#475569]">{description}</p>
        <div className="mt-8">{children}</div>
      </section>
    </main>
  );
}
