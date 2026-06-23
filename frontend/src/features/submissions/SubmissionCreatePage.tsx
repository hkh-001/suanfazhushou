"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { useProblem } from "@/features/problems/hooks";

import { useCreateSubmission } from "./hooks";
import type { SubmissionLanguage } from "./types";

const templates: Record<SubmissionLanguage, string> = {
  cpp: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    return 0;
}
`,
  python: `import sys

def solve() -> None:
    pass

if __name__ == "__main__":
    solve()
`
};

export function SubmissionCreatePage({ problemId }: { problemId: string }) {
  const router = useRouter();
  const problem = useProblem(problemId);
  const submission = useCreateSubmission();
  const [language, setLanguage] = useState<SubmissionLanguage>("cpp");
  const [sourceCode, setSourceCode] = useState(templates.cpp);

  function changeLanguage(nextLanguage: SubmissionLanguage) {
    setLanguage(nextLanguage);
    setSourceCode(templates[nextLanguage]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      const response = await submission.submit({
        problem_id: problemId,
        language,
        source_code: sourceCode
      });
      router.push(`/submissions/${response.data.id}`);
    } catch {
      // The hook owns the user-facing error state.
    }
  }

  if (problem.loading) {
    return (
      <AppShell>
        <section className="rounded-lg border border-blue-100 bg-white p-6 text-slate-500">正在加载题目...</section>
      </AppShell>
    );
  }

  if (problem.error || !problem.data) {
    return (
      <AppShell>
        <section className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-700">
          {problem.error ?? "题目不存在。"}
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        actions={
          <Link
            className="rounded-md border border-blue-200 bg-white px-4 py-2 text-sm font-semibold text-blue-700 hover:bg-blue-50"
            href={`/problems/${problemId}`}
          >
            返回题目
          </Link>
        }
        description={`为个人题库 #${problem.data.display_id}「${problem.data.title}」提交代码。代码只会发送到隔离 Judge 服务。`}
        title="提交代码"
      />

      <form className="grid gap-6 lg:grid-cols-[300px_minmax(0,1fr)]" onSubmit={(event) => void handleSubmit(event)}>
        <aside className="space-y-5 rounded-lg border border-blue-100 bg-white p-5 shadow-sm">
          <fieldset>
            <legend className="text-sm font-semibold text-slate-900">编程语言</legend>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {(["cpp", "python"] as const).map((item) => (
                <button
                  className={`rounded-md border px-3 py-2 text-sm font-semibold ${
                    language === item
                      ? "border-blue-600 bg-blue-600 text-white"
                      : "border-blue-200 bg-white text-blue-700 hover:bg-blue-50"
                  }`}
                  key={item}
                  onClick={() => changeLanguage(item)}
                  type="button"
                >
                  {item === "cpp" ? "C++17" : "Python 3.11"}
                </button>
              ))}
            </div>
          </fieldset>

          <div className="rounded-md border border-sky-200 bg-sky-50 p-4 text-sm leading-6 text-slate-600">
            <p className="font-semibold text-slate-900">安全执行说明</p>
            <p className="mt-2">
              提交代码将在无网络、只读系统文件和受限 CPU、内存、进程数的临时容器中执行。
            </p>
          </div>

          {submission.error ? (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700">{submission.error}</div>
          ) : null}

          <button
            className="w-full rounded-md bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={submission.loading || !sourceCode.trim()}
            type="submit"
          >
            {submission.loading ? "正在判题..." : "提交并判题"}
          </button>
        </aside>

        <section className="min-w-0 rounded-lg border border-blue-100 bg-slate-950 p-1 shadow-sm">
          <label className="sr-only" htmlFor="source-code">
            提交源码
          </label>
          <textarea
            className="min-h-[620px] w-full resize-y rounded-md border-0 bg-slate-950 p-5 font-mono text-sm leading-6 text-slate-100 outline-none focus:ring-2 focus:ring-blue-400"
            id="source-code"
            maxLength={20000}
            onChange={(event) => setSourceCode(event.target.value)}
            spellCheck={false}
            value={sourceCode}
          />
        </section>
      </form>
    </AppShell>
  );
}
