"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useDeleteProblem, useProblem, useUpdateProblem } from "./hooks";
import { emptyProblemForm, formStateFromProblem, payloadFromForm, ProblemForm } from "./ProblemFormPage";

export function ProblemDetailPage({ id }: { id: string }) {
  const router = useRouter();
  const { data, loading, error, reload } = useProblem(id);
  const updateProblem = useUpdateProblem(id);
  const deleteProblem = useDeleteProblem(id);
  const [state, setState] = useState(emptyProblemForm);

  useEffect(() => {
    if (data) {
      setState(formStateFromProblem(data));
    }
  }, [data]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    try {
      await updateProblem.submit(payloadFromForm(state));
      await reload();
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  async function handleDelete() {
    const confirmed = window.confirm("确认删除这道题目吗？删除后无法恢复。");
    if (!confirmed) {
      return;
    }
    try {
      await deleteProblem.submit();
      router.push("/problems");
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  if (loading) {
    return (
      <AppShell>
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b] shadow-sm shadow-blue-100/60">
          正在加载题目...
        </section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">题目加载失败</p>
          <p className="mt-2 text-sm">{error ?? "题目不存在，或你没有访问权限。"}</p>
          <button
            className="mt-4 font-semibold text-[#1d4ed8] underline-offset-4 hover:underline"
            onClick={() => void reload()}
            type="button"
          >
            重试
          </button>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        description={`编辑 #${data.display_id} 的题目内容、知识点关联和题解信息。当前 slug：${data.slug}`}
        title="编辑题目"
      />
      <ProblemForm
        error={updateProblem.error ?? deleteProblem.error}
        extraActions={
          <button
            className="rounded-md border border-red-200 bg-red-50 px-5 py-3 text-sm font-semibold text-red-700 outline-none transition hover:bg-red-100 focus-visible:ring-2 focus-visible:ring-red-200 disabled:opacity-60"
            disabled={deleteProblem.loading}
            onClick={() => void handleDelete()}
            type="button"
          >
            {deleteProblem.loading ? "正在删除..." : "删除题目"}
          </button>
        }
        loading={updateProblem.loading}
        onSubmit={(event) => void handleSubmit(event)}
        setState={setState}
        state={state}
        submitLabel="保存修改"
        success={updateProblem.success ? "题目已保存。" : null}
      />
    </AppShell>
  );
}
