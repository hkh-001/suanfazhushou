"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { formStateFromMistake, MistakeForm, payloadFromMistakeForm } from "./MistakeFormPage";
import { useDeleteMistakeNote, useMistakeNote, useUpdateMistakeNote } from "./hooks";

export function MistakeDetailPage({ id }: { id: string }) {
  const router = useRouter();
  const { data, loading, error, reload } = useMistakeNote(id);
  const { submit: update, loading: updating, error: updateError, success } = useUpdateMistakeNote(id);
  const { submit: remove, loading: deleting, error: deleteError } = useDeleteMistakeNote(id);
  const [state, setState] = useState(() => (data ? formStateFromMistake(data) : null));
  const displayData = data;
  const displayState = state ?? (data ? formStateFromMistake(data) : null);
  const canSubmit = Boolean(displayState?.title.trim() && displayState.root_cause.trim());

  useEffect(() => {
    if (data) {
      setState(formStateFromMistake(data));
    }
  }, [data]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!displayState || !canSubmit) {
      return;
    }
    try {
      await update(payloadFromMistakeForm(displayState));
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  async function handleDelete() {
    if (!window.confirm("确定删除这条复盘笔记吗？")) {
      return;
    }
    try {
      await remove();
      router.push("/mistakes");
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  if (loading) {
    return (
      <AppShell>
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b]">正在加载复盘笔记...</section>
      </AppShell>
    );
  }

  if (error || !displayData || !displayState) {
    return (
      <AppShell>
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">复盘笔记加载失败</p>
          <p className="mt-2 text-sm">{error ?? "暂时无法获取复盘笔记。"}</p>
          <button className="mt-4 rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white" onClick={() => void reload()} type="button">
            重试
          </button>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        actions={
          <>
            {displayData.problem ? (
              <Link className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8]" href={`/problems/${displayData.problem.id}`}>
                查看关联题目
              </Link>
            ) : null}
            {displayData.code_review ? (
              <Link className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8]" href={`/code-reviews/${displayData.code_review.id}`}>
                查看诊断记录
              </Link>
            ) : null}
          </>
        }
        description="编辑根因分析、修复建议和个人反思。保存后会停留在当前复盘页面。"
        title="编辑复盘笔记"
      />

      <MistakeForm
        error={updateError ?? deleteError}
        extraActions={
          <button className="rounded-md border border-red-200 bg-red-50 px-5 py-3 text-sm font-semibold text-red-700 disabled:opacity-60" disabled={deleting} onClick={() => void handleDelete()} type="button">
            {deleting ? "正在删除..." : "删除复盘"}
          </button>
        }
        loading={updating}
        onSubmit={(event) => void handleSubmit(event)}
        setState={setState}
        state={displayState}
        submitLabel="保存修改"
        success={success ? "复盘笔记已保存。" : null}
      />
    </AppShell>
  );
}
