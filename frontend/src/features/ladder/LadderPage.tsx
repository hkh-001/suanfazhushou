"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MarkdownContent } from "@/components/MarkdownContent";
import { PageHeader } from "@/components/PageHeader";

import { useCompleteLadderMaterial, useLadder, useLadderNode, useSubmitLadderPractice } from "./hooks";
import type {
  LadderChoicePracticeItem,
  LadderCodingPracticeItem,
  LadderNodeStatus,
  LadderNodeSummary,
  LadderPracticeSubmitResult,
  LadderSummary
} from "./types";

const statusLabels: Record<LadderNodeStatus, string> = {
  locked: "未解锁",
  unlocked: "可学习",
  material_done: "资料已读",
  practice_done: "练习完成",
  passed: "已通过"
};

const statusStyles: Record<LadderNodeStatus, string> = {
  locked: "border-slate-200 bg-slate-100 text-slate-500",
  unlocked: "border-blue-200 bg-blue-50 text-blue-700",
  material_done: "border-cyan-200 bg-cyan-50 text-cyan-700",
  practice_done: "border-amber-200 bg-amber-50 text-amber-700",
  passed: "border-emerald-200 bg-emerald-50 text-emerald-700"
};

const nodeDotStyles: Record<LadderNodeStatus, string> = {
  locked: "bg-slate-300",
  unlocked: "bg-blue-500",
  material_done: "bg-cyan-500",
  practice_done: "bg-amber-500",
  passed: "bg-emerald-500"
};

function flattenNodes(summary: LadderSummary | null): LadderNodeSummary[] {
  return summary?.phases.flatMap((phase) => phase.nodes) ?? [];
}

function findNode(summary: LadderSummary | null, nodeId: string | null) {
  if (!summary || !nodeId) {
    return null;
  }
  return flattenNodes(summary).find((node) => node.id === nodeId) ?? null;
}

function nodeLabel(node: LadderNodeSummary) {
  return `第 ${node.node_index} 阶`;
}

function EmptyPanel({ message }: { message: string }) {
  return (
    <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
      {message}
    </section>
  );
}

function splitPracticeItems(items: NonNullable<ReturnType<typeof useLadderNode>["data"]>["practice_items"]) {
  return {
    choiceItems: items.filter((item): item is LadderChoicePracticeItem => item.type === "choice"),
    codingItems: items.filter((item): item is LadderCodingPracticeItem => item.type === "coding")
  };
}

export function LadderPage() {
  const { data, loading, error, reload, setData } = useLadder();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const selectedSummary = useMemo(() => findNode(data, selectedNodeId), [data, selectedNodeId]);
  const { data: nodeDetail, loading: nodeLoading, error: nodeError, reload: reloadNode } = useLadderNode(selectedNodeId);
  const { complete, loading: completing, error: completeError } = useCompleteLadderMaterial();
  const { submit, loading: submitting, error: submitError } = useSubmitLadderPractice();
  const [choiceAnswers, setChoiceAnswers] = useState<Record<string, string>>({});
  const [completedCodingIds, setCompletedCodingIds] = useState<string[]>([]);
  const [practiceResult, setPracticeResult] = useState<LadderPracticeSubmitResult | null>(null);

  useEffect(() => {
    if (!data) {
      return;
    }
    const nodes = flattenNodes(data);
    if (!selectedNodeId || !nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(data.current_node_id ?? nodes[0]?.id ?? null);
    }
  }, [data, selectedNodeId]);

  useEffect(() => {
    setChoiceAnswers({});
    setCompletedCodingIds([]);
    setPracticeResult(null);
  }, [nodeDetail?.id]);

  async function handleComplete() {
    if (!selectedNodeId) {
      return;
    }
    try {
      const updated = await complete(selectedNodeId);
      setData(updated);
      await reloadNode();
    } catch {
      // The hook exposes the user-facing error message.
    }
  }

  async function handlePracticeSubmit() {
    if (!selectedNodeId) {
      return;
    }
    try {
      const result = await submit(selectedNodeId, {
        choice_answers: Object.entries(choiceAnswers).map(([item_id, option_id]) => ({ item_id, option_id })),
        completed_coding_item_ids: completedCodingIds
      });
      setPracticeResult(result);
      setData(result.ladder);
      await reloadNode();
    } catch {
      // The hook exposes the user-facing error message.
    }
  }

  function toggleCodingItem(itemId: string) {
    setCompletedCodingIds((current) =>
      current.includes(itemId) ? current.filter((id) => id !== itemId) : [...current, itemId]
    );
  }

  if (loading) {
    return (
      <AppShell>
        <EmptyPanel message="正在加载学习天梯..." />
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell maxWidth="max-w-6xl">
        <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
          <h1 className="text-2xl font-semibold text-[#0f172a]">学习天梯</h1>
          <p className="mt-3 text-sm font-semibold text-red-700">{error ?? "学习天梯加载失败。"}</p>
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

  const nodeCount = flattenNodes(data).length;
  const practiceItems = nodeDetail?.practice_items ?? [];
  const { choiceItems, codingItems } = splitPracticeItems(practiceItems);
  const practiceBlockedByMaterial = Boolean(nodeDetail && !nodeDetail.locked && !nodeDetail.material_completed);
  const practiceUnavailable = Boolean(nodeDetail?.locked || practiceBlockedByMaterial || practiceItems.length === 0);
  const practiceCompleted = Boolean(nodeDetail?.practice_completed);

  return (
    <AppShell>
      <PageHeader
        description="根据你的学习目标和当前水平，逐步点亮算法学习路径。"
        title="学习天梯"
        actions={
          <Link
            className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href="/dashboard"
          >
            返回看板
          </Link>
        }
      />

      <section className="mb-6 rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-[#2563eb]">{data.path.template_name}</p>
            <h2 className="mt-2 text-2xl font-semibold text-[#0f172a]">当前路径</h2>
          </div>
          <div className="flex flex-wrap gap-2 text-sm">
            <span className="rounded-full bg-[#eff6ff] px-3 py-1 font-semibold text-[#1d4ed8]">
              {data.path.goal_track}
            </span>
            <span className="rounded-full bg-[#eff6ff] px-3 py-1 font-semibold text-[#1d4ed8]">
              {data.path.current_level}
            </span>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1.45fr)]">
        <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
          <div className="mb-5 flex items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-[#0f172a]">路径节点</h2>
            <span className="text-sm text-[#64748b]">{nodeCount} 个节点</span>
          </div>

          <div className="space-y-6">
            {data.phases.map((phase) => (
              <div key={phase.phase_index}>
                <div className="mb-3">
                  <h3 className="font-semibold text-[#0f172a]">{phase.title}</h3>
                  {phase.description ? <p className="mt-1 text-sm text-[#64748b]">{phase.description}</p> : null}
                </div>
                <div className="space-y-3">
                  {phase.nodes.map((node) => {
                    const selected = node.id === selectedNodeId;
                    return (
                      <button
                        className={`grid w-full grid-cols-[28px_1fr] gap-3 rounded-lg border p-3 text-left outline-none transition focus-visible:ring-2 focus-visible:ring-[#93c5fd] ${
                          selected
                            ? "border-[#2563eb] bg-[#eff6ff] shadow-sm shadow-blue-100"
                            : "border-[#dbeafe] bg-white hover:border-[#93c5fd] hover:bg-[#f8fbff]"
                        }`}
                        key={node.id}
                        onClick={() => setSelectedNodeId(node.id)}
                        type="button"
                      >
                        <span
                          className={`mt-1 flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white ${
                            nodeDotStyles[node.status]
                          }`}
                        >
                          {node.node_index}
                        </span>
                        <span>
                          <span className="flex flex-wrap items-center gap-2">
                            <span className="font-semibold text-[#0f172a]">{node.title}</span>
                            <span className={`rounded-full border px-2 py-0.5 text-xs ${statusStyles[node.status]}`}>
                              {statusLabels[node.status]}
                            </span>
                          </span>
                          <span className="mt-1 block text-sm text-[#64748b]">{node.summary}</span>
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
          {nodeLoading ? <p className="text-[#64748b]">正在加载节点资料...</p> : null}
          {nodeError ? <p className="text-sm font-semibold text-red-700">{nodeError}</p> : null}
          {!nodeLoading && !nodeError && selectedSummary && nodeDetail ? (
            <div>
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e2e8f0] pb-5">
                <div>
                  <p className="text-sm font-semibold text-[#2563eb]">{nodeLabel(selectedSummary)}</p>
                  <h2 className="mt-2 text-2xl font-semibold text-[#0f172a]">{nodeDetail.title}</h2>
                  <p className="mt-2 text-[#64748b]">{nodeDetail.summary}</p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-sm font-semibold ${statusStyles[nodeDetail.status]}`}>
                  {statusLabels[nodeDetail.status]}
                </span>
              </div>

              <div className="mt-6 rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-4">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <h3 className="text-lg font-semibold text-[#0f172a]">资料阅读</h3>
                  {nodeDetail.material_completed ? (
                    <span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700">资料已读</span>
                  ) : null}
                </div>
                <div className="rounded-lg bg-white p-4">
                  <MarkdownContent content={nodeDetail.material_markdown} />
                </div>

                {nodeDetail.resource_links.length > 0 ? (
                  <div className="mt-4">
                    <h4 className="font-semibold text-[#0f172a]">参考资料</h4>
                    <div className="mt-3 space-y-2">
                      {nodeDetail.resource_links.map((link) => (
                        <a
                          className="block rounded-md border border-[#dbeafe] bg-white px-3 py-2 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                          href={link.url}
                          key={`${link.title}-${link.url}`}
                          rel="noreferrer noopener"
                          target="_blank"
                        >
                          {link.title}
                          {link.source ? <span className="ml-2 font-normal text-[#64748b]">({link.source})</span> : null}
                        </a>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div className="mt-5 flex flex-wrap items-center gap-3">
                  <button
                    className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                    disabled={nodeDetail.locked || nodeDetail.material_completed || completing}
                    onClick={() => void handleComplete()}
                    type="button"
                  >
                    {nodeDetail.material_completed ? "资料已读" : completing ? "正在保存..." : "标记资料已读"}
                  </button>
                  {nodeDetail.locked ? <span className="text-sm text-[#64748b]">完成前置节点资料后解锁</span> : null}
                  {completeError ? <span className="text-sm font-semibold text-red-700">{completeError}</span> : null}
                </div>
              </div>

              <div className="mt-6 rounded-lg border border-[#dbeafe] bg-white p-4">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-[#0f172a]">节点练习</h3>
                    <p className="mt-1 text-sm text-[#64748b]">选择题由后端判分，编程题仅做自查确认，不运行代码。</p>
                  </div>
                  {practiceCompleted ? (
                    <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">练习已完成</span>
                  ) : null}
                </div>

                {nodeDetail.locked ? (
                  <EmptyPanel message="完成前置节点资料后解锁练习。" />
                ) : practiceBlockedByMaterial ? (
                  <EmptyPanel message="先完成资料阅读后再开始练习。" />
                ) : practiceItems.length === 0 ? (
                  <EmptyPanel message="当前节点暂未配置练习。" />
                ) : (
                  <div className="space-y-5">
                    {choiceItems.map((item, index) => {
                      const result = practiceResult?.choice_results.find((choiceResult) => choiceResult.item_id === item.id);
                      return (
                        <div className="rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-4" key={item.id}>
                          <p className="text-sm font-semibold text-[#2563eb]">选择题 {index + 1}</p>
                          <h4 className="mt-2 font-semibold text-[#0f172a]">{item.prompt}</h4>
                          <div className="mt-3 space-y-2">
                            {item.options.map((option) => (
                              <label
                                className="flex cursor-pointer items-start gap-3 rounded-md border border-[#dbeafe] bg-white px-3 py-2 text-sm text-[#0f172a] hover:bg-[#eff6ff]"
                                key={option.id}
                              >
                                <input
                                  checked={choiceAnswers[item.id] === option.id}
                                  className="mt-1"
                                  disabled={practiceCompleted}
                                  name={item.id}
                                  onChange={() => setChoiceAnswers((current) => ({ ...current, [item.id]: option.id }))}
                                  type="radio"
                                />
                                <span>{option.text}</span>
                              </label>
                            ))}
                          </div>
                          {result ? (
                            <div
                              className={`mt-3 rounded-md border px-3 py-2 text-sm ${
                                result.correct
                                  ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                                  : "border-red-200 bg-red-50 text-red-700"
                              }`}
                            >
                              {result.correct ? "回答正确" : "回答错误"}
                              {result.explanation ? <span className="mt-1 block">{result.explanation}</span> : null}
                            </div>
                          ) : null}
                        </div>
                      );
                    })}

                    {codingItems.map((item, index) => (
                      <div className="rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-4" key={item.id}>
                        <p className="text-sm font-semibold text-[#2563eb]">编程自查 {index + 1}</p>
                        <h4 className="mt-2 font-semibold text-[#0f172a]">{item.prompt}</h4>
                        <p className="mt-2 rounded-md bg-white px-3 py-2 text-sm text-[#475569]">{item.self_check}</p>
                        <label className="mt-3 flex cursor-pointer items-center gap-2 text-sm font-semibold text-[#0f172a]">
                          <input
                            checked={completedCodingIds.includes(item.id)}
                            disabled={practiceCompleted}
                            onChange={() => toggleCodingItem(item.id)}
                            type="checkbox"
                          />
                          我已完成自查
                        </label>
                      </div>
                    ))}

                    {practiceResult ? (
                      <div
                        className={`rounded-lg border p-4 ${
                          practiceResult.passed
                            ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                            : "border-amber-200 bg-amber-50 text-amber-800"
                        }`}
                      >
                        <p className="font-semibold">
                          本次得分：{practiceResult.score} 分，{practiceResult.passed ? "已通过" : "未通过"}
                        </p>
                        {!practiceResult.passed ? <p className="mt-1 text-sm">请根据解释重新答题并确认自查。</p> : null}
                      </div>
                    ) : null}

                    {submitError ? <p className="text-sm font-semibold text-red-700">{submitError}</p> : null}

                    <button
                      className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                      disabled={practiceUnavailable || practiceCompleted || submitting}
                      onClick={() => void handlePracticeSubmit()}
                      type="button"
                    >
                      {practiceCompleted ? "练习已完成" : submitting ? "正在提交..." : "提交练习"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}
