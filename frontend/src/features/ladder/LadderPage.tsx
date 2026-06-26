"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { MarkdownContent } from "@/components/MarkdownContent";
import { PageHeader } from "@/components/PageHeader";

import {
  useCompleteLadderMaterial,
  useGenerateLadderExam,
  useLadder,
  useLadderNode,
  useSubmitLadderExam,
  useSubmitLadderPractice
} from "./hooks";
import type {
  LadderChoicePracticeItem,
  LadderCodingPracticeItem,
  LadderExamAttempt,
  LadderExamQuestionResult,
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

const goalTrackLabels: Record<string, string> = {
  course: "课程提分",
  lanqiao: "蓝桥杯",
  icpc: "ICPC/CCPC",
  self_study: "自学提升"
};

const levelLabels: Record<string, string> = {
  beginner: "0 基础",
  elementary: "入门",
  popularization: "普及",
  improvement: "提高"
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

function resultMap(attempt: LadderExamAttempt | null): Record<string, LadderExamQuestionResult> {
  return Object.fromEntries((attempt?.results ?? []).map((result) => [result.question_id, result]));
}

export function LadderPage() {
  const searchParams = useSearchParams();
  const initialNodeId = searchParams.get("node_id");
  const { data, loading, error, reload, setData } = useLadder();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const selectedSummary = useMemo(() => findNode(data, selectedNodeId), [data, selectedNodeId]);
  const { data: nodeDetail, loading: nodeLoading, error: nodeError, reload: reloadNode } = useLadderNode(selectedNodeId);
  const { complete, loading: completing, error: completeError } = useCompleteLadderMaterial();
  const { submit: submitPractice, loading: submittingPractice, error: submitPracticeError } = useSubmitLadderPractice();
  const { generate, loading: generatingExam, error: generateExamError } = useGenerateLadderExam();
  const { submit: submitExam, loading: submittingExam, error: submitExamError } = useSubmitLadderExam();
  const [choiceAnswers, setChoiceAnswers] = useState<Record<string, string>>({});
  const [completedCodingIds, setCompletedCodingIds] = useState<string[]>([]);
  const [practiceResult, setPracticeResult] = useState<LadderPracticeSubmitResult | null>(null);
  const [examAttempt, setExamAttempt] = useState<LadderExamAttempt | null>(null);
  const [examAnswers, setExamAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!data) {
      return;
    }
    const nodes = flattenNodes(data);
    const requestedNode = initialNodeId && nodes.some((node) => node.id === initialNodeId) ? initialNodeId : null;
    if (!selectedNodeId || !nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(requestedNode ?? data.current_node_id ?? nodes[0]?.id ?? null);
    }
  }, [data, initialNodeId, selectedNodeId]);

  useEffect(() => {
    setChoiceAnswers({});
    setCompletedCodingIds([]);
    setPracticeResult(null);
    setExamAttempt(null);
    setExamAnswers({});
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
      const result = await submitPractice(selectedNodeId, {
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

  async function handleGenerateExam() {
    if (!selectedNodeId) {
      return;
    }
    try {
      const result = await generate(selectedNodeId);
      setExamAttempt(result.attempt);
      setExamAnswers({});
    } catch {
      // The hook exposes the user-facing error message.
    }
  }

  async function handleExamSubmit() {
    if (!examAttempt) {
      return;
    }
    try {
      const result = await submitExam(examAttempt.id, {
        answers: Object.entries(examAnswers).map(([question_id, option_id]) => ({ question_id, option_id }))
      });
      setExamAttempt(result.attempt);
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
  const examBlockedByMaterial = Boolean(nodeDetail && !nodeDetail.material_completed);
  const examBlockedByPractice = Boolean(nodeDetail && nodeDetail.material_completed && !nodeDetail.practice_completed);
  const examPassed = Boolean(nodeDetail?.exam_passed);
  const examResults = resultMap(examAttempt);
  const canSubmitExam = Boolean(
    examAttempt &&
      examAttempt.status === "generated" &&
      examAttempt.questions.every((question) => Boolean(examAnswers[question.id]))
  );

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
              {goalTrackLabels[data.path.goal_track] ?? data.path.goal_track}
            </span>
            <span className="rounded-full bg-[#f8fafc] px-3 py-1 font-semibold text-[#475569]">
              {levelLabels[data.path.current_level] ?? data.path.current_level}
            </span>
            <span className="rounded-full bg-[#f8fafc] px-3 py-1 font-semibold text-[#475569]">
              共 {nodeCount} 个节点
            </span>
          </div>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1.45fr)]">
        <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
          <h2 className="text-xl font-semibold text-[#0f172a]">路径节点</h2>
          <div className="mt-5 space-y-6">
            {data.phases.map((phase) => (
              <div key={phase.phase_index}>
                <div className="mb-3">
                  <h3 className="text-base font-semibold text-[#0f172a]">
                    阶段 {phase.phase_index}：{phase.title}
                  </h3>
                  <p className="mt-1 text-sm text-[#64748b]">{phase.description}</p>
                </div>
                <div className="space-y-3">
                  {phase.nodes.map((node) => {
                    const selected = node.id === selectedNodeId;
                    return (
                      <button
                        className={`w-full rounded-lg border p-4 text-left transition ${
                          selected
                            ? "border-[#2563eb] bg-[#eff6ff] shadow-sm shadow-blue-100"
                            : "border-[#dbeafe] bg-white hover:border-[#93c5fd]"
                        }`}
                        key={node.id}
                        onClick={() => setSelectedNodeId(node.id)}
                        type="button"
                      >
                        <div className="flex items-start gap-3">
                          <span
                            className={`mt-1 h-3 w-3 shrink-0 rounded-full ${nodeDotStyles[node.status]}`}
                            aria-hidden="true"
                          />
                          <span className="min-w-0 flex-1">
                            <span className="flex flex-wrap items-center gap-2">
                              <span className="text-sm font-semibold text-[#1e3a8a]">{nodeLabel(node)}</span>
                              <span className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${statusStyles[node.status]}`}>
                                {statusLabels[node.status]}
                              </span>
                            </span>
                            <span className="mt-1 block text-base font-semibold text-[#0f172a]">{node.title}</span>
                            <span className="mt-1 line-clamp-2 block text-sm text-[#64748b]">{node.summary}</span>
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="space-y-5">
          {!selectedSummary ? <EmptyPanel message="请选择一个节点查看详情。" /> : null}

          {selectedSummary ? (
            <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-[#2563eb]">{nodeLabel(selectedSummary)}</p>
                  <h2 className="mt-2 text-2xl font-semibold text-[#0f172a]">{selectedSummary.title}</h2>
                  <p className="mt-2 text-sm text-[#64748b]">{selectedSummary.summary}</p>
                </div>
                <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${statusStyles[selectedSummary.status]}`}>
                  {statusLabels[selectedSummary.status]}
                </span>
              </div>
            </section>
          ) : null}

          {nodeLoading ? <EmptyPanel message="正在加载节点资料..." /> : null}
          {nodeError ? <EmptyPanel message={nodeError} /> : null}

          {nodeDetail ? (
            <>
              <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <h3 className="text-xl font-semibold text-[#0f172a]">资料阅读</h3>
                  {nodeDetail.material_completed ? (
                    <span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700">资料已读</span>
                  ) : null}
                </div>
                {nodeDetail.locked ? (
                  <p className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    通过前置节点考试后解锁。
                  </p>
                ) : (
                  <>
                    <div className="mt-5 overflow-x-auto">
                      <MarkdownContent content={nodeDetail.material_markdown} />
                    </div>
                    {nodeDetail.resource_links.length > 0 ? (
                      <div className="mt-6">
                        <h4 className="text-sm font-semibold text-[#0f172a]">参考链接</h4>
                        <ul className="mt-3 space-y-2">
                          {nodeDetail.resource_links.map((link) => (
                            <li key={`${link.url}-${link.title}`}>
                              <a
                                className="text-sm font-semibold text-[#2563eb] hover:text-[#1d4ed8]"
                                href={link.url}
                                rel="noreferrer"
                                target="_blank"
                              >
                                {link.title}
                              </a>
                              {link.source ? <span className="ml-2 text-xs text-[#94a3b8]">{link.source}</span> : null}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                    <div className="mt-6 flex flex-wrap items-center gap-3">
                      <button
                        className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                        disabled={completing || nodeDetail.material_completed}
                        onClick={() => void handleComplete()}
                        type="button"
                      >
                        {nodeDetail.material_completed ? "资料已读" : completing ? "正在保存..." : "标记资料已读"}
                      </button>
                      {completeError ? <span className="text-sm font-semibold text-red-700">{completeError}</span> : null}
                    </div>
                  </>
                )}
              </section>

              <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-xl font-semibold text-[#0f172a]">节点练习</h3>
                    <p className="mt-1 text-sm text-[#64748b]">选择题由后端判分，编程题仅做自查确认。</p>
                  </div>
                  {practiceCompleted ? (
                    <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700">练习已完成</span>
                  ) : null}
                </div>

                {nodeDetail.locked ? (
                  <p className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    通过前置节点考试后解锁练习。
                  </p>
                ) : practiceBlockedByMaterial ? (
                  <p className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-[#1e3a8a]">
                    先完成资料阅读后再开始练习。
                  </p>
                ) : practiceItems.length === 0 ? (
                  <p className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    当前节点暂未配置练习。
                  </p>
                ) : (
                  <div className="mt-5 space-y-5">
                    {choiceItems.map((item, index) => {
                      const result = practiceResult?.choice_results.find((entry) => entry.item_id === item.id);
                      return (
                        <div className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] p-4" key={item.id}>
                          <p className="text-sm font-semibold text-[#0f172a]">
                            {index + 1}. {item.prompt}
                          </p>
                          <div className="mt-3 grid gap-2">
                            {item.options.map((option) => (
                              <label className="flex cursor-pointer items-start gap-2 rounded-md border border-[#dbeafe] bg-white px-3 py-2 text-sm text-[#334155]" key={option.id}>
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
                            <div className={`mt-3 rounded-md border px-3 py-2 text-sm ${result.correct ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700"}`}>
                              <p className="font-semibold">{result.correct ? "回答正确" : "回答错误"}</p>
                              <p className="mt-1">{result.explanation}</p>
                            </div>
                          ) : null}
                        </div>
                      );
                    })}

                    {codingItems.map((item) => (
                      <label className="block rounded-lg border border-[#e2e8f0] bg-[#f8fafc] p-4" key={item.id}>
                        <span className="text-sm font-semibold text-[#0f172a]">{item.prompt}</span>
                        <span className="mt-2 block text-sm text-[#64748b]">{item.self_check}</span>
                        <span className="mt-3 flex items-center gap-2 text-sm font-semibold text-[#1e3a8a]">
                          <input
                            checked={completedCodingIds.includes(item.id)}
                            disabled={practiceCompleted}
                            onChange={() => toggleCodingItem(item.id)}
                            type="checkbox"
                          />
                          我已完成自查
                        </span>
                      </label>
                    ))}

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                        disabled={practiceUnavailable || practiceCompleted || submittingPractice}
                        onClick={() => void handlePracticeSubmit()}
                        type="button"
                      >
                        {practiceCompleted ? "练习已完成" : submittingPractice ? "正在提交..." : "提交练习"}
                      </button>
                      {submitPracticeError ? <span className="text-sm font-semibold text-red-700">{submitPracticeError}</span> : null}
                    </div>

                    {practiceResult ? (
                      <div className={`rounded-lg border p-4 text-sm ${practiceResult.passed ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                        <p className="font-semibold">
                          得分 {practiceResult.score} 分，{practiceResult.passed ? "练习通过" : "暂未通过"}
                        </p>
                        {!practiceResult.passed ? <p className="mt-1">可以调整答案后再次提交。</p> : null}
                      </div>
                    ) : null}
                  </div>
                )}
              </section>

              <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-xl font-semibold text-[#0f172a]">节点考试</h3>
                    <p className="mt-1 text-sm text-[#64748b]">
                      AI 只生成题目，后端按答案键确定性判分；代码题为阅读或补全选择题。
                    </p>
                  </div>
                  {examPassed ? (
                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">考试已通过</span>
                  ) : null}
                </div>

                {nodeDetail.locked ? (
                  <p className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                    通过前置节点考试后解锁。
                  </p>
                ) : examBlockedByMaterial ? (
                  <p className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-[#1e3a8a]">
                    先完成资料阅读后再参加考试。
                  </p>
                ) : examBlockedByPractice ? (
                  <p className="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-[#1e3a8a]">
                    先通过节点练习后再参加考试。
                  </p>
                ) : examPassed ? (
                  <p className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-semibold text-emerald-700">
                    你已通过该节点考试，下一节点已解锁。
                  </p>
                ) : (
                  <div className="mt-5 space-y-5">
                    {!examAttempt ? (
                      <div className="rounded-lg border border-blue-100 bg-blue-50 p-4 text-sm text-[#1e3a8a]">
                        <p className="font-semibold">考试包含 10 道单选题和 2 道代码阅读题，80 分通过。</p>
                        <p className="mt-1">生成考试会调用 AI 服务，未提交的考试会被复用。</p>
                      </div>
                    ) : null}

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                        disabled={generatingExam || Boolean(examAttempt && examAttempt.status === "generated")}
                        onClick={() => void handleGenerateExam()}
                        type="button"
                      >
                        {generatingExam ? "正在生成..." : examAttempt?.status === "generated" ? "考试已生成" : "生成考试"}
                      </button>
                      {examAttempt?.status === "submitted" && !examAttempt.passed ? (
                        <button
                          className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                          disabled={generatingExam}
                          onClick={() => {
                            setExamAttempt(null);
                            setExamAnswers({});
                            void handleGenerateExam();
                          }}
                          type="button"
                        >
                          重新生成考试
                        </button>
                      ) : null}
                      {generateExamError ? <span className="text-sm font-semibold text-red-700">{generateExamError}</span> : null}
                    </div>

                    {examAttempt ? (
                      <div className="space-y-4">
                        {examAttempt.status === "submitted" ? (
                          <div className={`rounded-lg border p-4 text-sm ${examAttempt.passed ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-amber-200 bg-amber-50 text-amber-700"}`}>
                            <p className="font-semibold">
                              得分 {examAttempt.score ?? 0} 分，{examAttempt.passed ? "考试通过" : "暂未通过"}
                            </p>
                            {!examAttempt.passed ? <p className="mt-1">可以重新生成考试后再次挑战。</p> : null}
                          </div>
                        ) : null}

                        {examAttempt.questions.map((question, index) => {
                          const result = examResults[question.id];
                          return (
                            <div className="rounded-lg border border-[#e2e8f0] bg-[#f8fafc] p-4" key={question.id}>
                              <div className="flex flex-wrap items-start justify-between gap-2">
                                <p className="text-sm font-semibold text-[#0f172a]">
                                  {index + 1}. {question.prompt}
                                </p>
                                <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-[#64748b]">
                                  {question.type === "code_reading" ? "代码阅读 20 分" : "单选 6 分"}
                                </span>
                              </div>
                              <div className="mt-3 grid gap-2">
                                {question.options.map((option) => {
                                  const selected = examAnswers[question.id] === option.id;
                                  const submittedSelected = result?.selected_option_id === option.id;
                                  const correct = result?.correct_option_id === option.id;
                                  return (
                                    <label
                                      className={`flex cursor-pointer items-start gap-2 rounded-md border bg-white px-3 py-2 text-sm text-[#334155] ${correct ? "border-emerald-300" : submittedSelected ? "border-amber-300" : "border-[#dbeafe]"}`}
                                      key={option.id}
                                    >
                                      <input
                                        checked={selected}
                                        disabled={examAttempt.status === "submitted"}
                                        name={question.id}
                                        onChange={() => setExamAnswers((current) => ({ ...current, [question.id]: option.id }))}
                                        type="radio"
                                      />
                                      <span>{option.text}</span>
                                    </label>
                                  );
                                })}
                              </div>
                              {result ? (
                                <div className={`mt-3 rounded-md border px-3 py-2 text-sm ${result.correct ? "border-emerald-200 bg-emerald-50 text-emerald-700" : "border-red-200 bg-red-50 text-red-700"}`}>
                                  <p className="font-semibold">
                                    {result.correct ? "回答正确" : "回答错误"}，本题 {result.points} 分
                                  </p>
                                  <p className="mt-1">正确答案：{result.correct_option_id}</p>
                                  <p className="mt-1">{result.explanation}</p>
                                </div>
                              ) : null}
                            </div>
                          );
                        })}

                        {examAttempt.status === "generated" ? (
                          <div className="flex flex-wrap items-center gap-3">
                            <button
                              className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white outline-none hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-[#bfdbfe] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                              disabled={!canSubmitExam || submittingExam}
                              onClick={() => void handleExamSubmit()}
                              type="button"
                            >
                              {submittingExam ? "正在提交..." : "提交考试"}
                            </button>
                            {!canSubmitExam ? <span className="text-sm text-[#64748b]">请完成全部 12 道题后提交。</span> : null}
                            {submitExamError ? <span className="text-sm font-semibold text-red-700">{submitExamError}</span> : null}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                )}
              </section>
            </>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}
