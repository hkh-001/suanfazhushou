"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MarkdownContent } from "@/components/MarkdownContent";
import { PageHeader } from "@/components/PageHeader";

import { useCompleteLadderMaterial, useLadder, useLadderNode } from "./hooks";
import type { LadderNodeStatus, LadderNodeSummary, LadderSummary } from "./types";

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

export function LadderPage() {
  const { data, loading, error, reload, setData } = useLadder();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const selectedSummary = useMemo(() => findNode(data, selectedNodeId), [data, selectedNodeId]);
  const { data: nodeDetail, loading: nodeLoading, error: nodeError, reload: reloadNode } = useLadderNode(selectedNodeId);
  const { complete, loading: completing, error: completeError } = useCompleteLadderMaterial();

  useEffect(() => {
    if (!data) {
      return;
    }
    const nodes = flattenNodes(data);
    if (!selectedNodeId || !nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(data.current_node_id ?? nodes[0]?.id ?? null);
    }
  }, [data, selectedNodeId]);

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
            <span className="text-sm text-[#64748b]">{flattenNodes(data).length} 个节点</span>
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

              <div className="mt-6">
                <MarkdownContent content={nodeDetail.material_markdown} />
              </div>

              {nodeDetail.resource_links.length > 0 ? (
                <div className="mt-6 rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-4">
                  <h3 className="font-semibold text-[#0f172a]">参考资料</h3>
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

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <button
                  className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                  disabled={nodeDetail.locked || nodeDetail.material_completed || completing}
                  onClick={() => void handleComplete()}
                  type="button"
                >
                  {nodeDetail.material_completed ? "资料已读" : completing ? "正在保存..." : "标记资料已读"}
                </button>
                {nodeDetail.locked ? (
                  <span className="text-sm text-[#64748b]">完成前置节点资料后解锁</span>
                ) : null}
                {completeError ? <span className="text-sm font-semibold text-red-700">{completeError}</span> : null}
              </div>
            </div>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}
