"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";

import { useCodeReview, useDeleteCodeReview } from "./hooks";

export function CodeReviewDetailPage({ id }: { id: string }) {
  const router = useRouter();
  const { data, loading, error, reload } = useCodeReview(id);
  const { submit: deleteReview, loading: deleting, error: deleteError } = useDeleteCodeReview(id);

  async function handleDelete() {
    if (!window.confirm("确定删除这条诊断记录吗？关联复盘笔记会保留。")) {
      return;
    }
    try {
      await deleteReview();
      router.push("/code-reviews");
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  if (loading) {
    return (
      <AppShell>
        <section className="rounded-xl border border-[#dbeafe] bg-white/90 p-6 text-[#64748b]">正在加载诊断详情...</section>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <section className="rounded-xl border border-red-200 bg-red-50 p-6 text-red-700">
          <p className="font-semibold">诊断详情加载失败</p>
          <p className="mt-2 text-sm">{error ?? "暂时无法获取诊断详情。"}</p>
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
            <Link className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8]" href="/code-reviews">
              返回诊断记录
            </Link>
            <Link className="rounded-md bg-[#2563eb] px-4 py-2 text-sm font-semibold text-white" href={`/mistakes/new?code_review_id=${data.id}`}>
              创建复盘笔记
            </Link>
          </>
        }
        description="查看用户显式保存的代码、AI 分析和关联信息。"
        title="诊断详情"
      />

      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <aside className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
          <h2 className="text-lg font-semibold text-[#0f172a]">记录信息</h2>
          <dl className="mt-4 grid gap-3 text-sm">
            <div>
              <dt className="font-semibold text-[#64748b]">语言</dt>
              <dd>{data.language === "cpp" ? "C++" : "Python"}</dd>
            </div>
            <div>
              <dt className="font-semibold text-[#64748b]">保存时间</dt>
              <dd>{new Date(data.created_at).toLocaleString("zh-CN")}</dd>
            </div>
            <div>
              <dt className="font-semibold text-[#64748b]">模型</dt>
              <dd>{data.model ?? "-"}</dd>
            </div>
            <div>
              <dt className="font-semibold text-[#64748b]">Token</dt>
              <dd>
                输入 {data.input_tokens ?? "-"} / 输出 {data.output_tokens ?? "-"}
              </dd>
            </div>
            {data.topic ? (
              <div>
                <dt className="font-semibold text-[#64748b]">知识点</dt>
                <dd>{data.topic.title}</dd>
              </div>
            ) : null}
            {data.problem ? (
              <div>
                <dt className="font-semibold text-[#64748b]">关联题目</dt>
                <dd>
                  <Link className="font-semibold text-[#2563eb]" href={`/problems/${data.problem.id}`}>
                    #{data.problem.display_id} {data.problem.title}
                  </Link>
                </dd>
              </div>
            ) : null}
          </dl>
          {deleteError ? <p className="mt-4 text-sm font-semibold text-red-700">{deleteError}</p> : null}
          <button className="mt-5 rounded-md border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-60" disabled={deleting} onClick={() => void handleDelete()} type="button">
            {deleting ? "正在删除..." : "删除诊断记录"}
          </button>
        </aside>

        <section className="grid gap-5">
          {data.question ? (
            <div className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
              <h2 className="font-semibold text-[#0f172a]">补充问题</h2>
              <p className="mt-3 whitespace-pre-wrap text-sm leading-7 text-[#334155]">{data.question}</p>
            </div>
          ) : null}
          <div className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="font-semibold text-[#0f172a]">保存的代码</h2>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words rounded-lg bg-[#0f172a] p-4 font-mono text-sm leading-6 text-[#e0f2fe]">{data.code}</pre>
          </div>
          <div className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
            <h2 className="font-semibold text-[#0f172a]">AI 分析结果</h2>
            <pre className="mt-3 whitespace-pre-wrap break-words font-sans text-sm leading-7 text-[#334155]">{data.analysis_result}</pre>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
