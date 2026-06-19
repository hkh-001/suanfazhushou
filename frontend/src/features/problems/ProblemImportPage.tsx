"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { isAuthRequiredError } from "@/features/auth/hooks";
import { ApiError } from "@/lib/api/client";

import { useImportProblemZip } from "./hooks";

function getImportErrorMessage(error: unknown): string {
  if (isAuthRequiredError(error)) {
    return "请先登录后再导入个人题库。";
  }
  if (error instanceof ApiError) {
    const messages: Record<string, string> = {
      ZIP_FILE_REQUIRED: "请选择一个 ZIP 文件。",
      ZIP_INVALID_ARCHIVE: "上传的文件不是有效 ZIP 压缩包。",
      ZIP_ARCHIVE_EMPTY: "ZIP 压缩包是空的，请检查内容。",
      ZIP_FILE_TOO_LARGE: "ZIP 文件或其中某个文件超出大小限制。",
      ZIP_FILE_COUNT_EXCEEDED: "ZIP 中的文件数量过多。",
      ZIP_UNCOMPRESSED_SIZE_EXCEEDED: "ZIP 解压后的内容过大。",
      ZIP_COMPRESSION_RATIO_EXCEEDED: "ZIP 压缩比异常，可能存在安全风险。",
      ZIP_PATH_NOT_ALLOWED: "ZIP 中包含不允许的路径结构。",
      ZIP_FILE_TYPE_NOT_ALLOWED: "ZIP 中包含不支持的文件类型。",
      ZIP_DUPLICATE_PATH: "ZIP 中存在重复路径。",
      ZIP_INVALID_ENCODING: "ZIP 中的文本文件必须使用 UTF-8 编码。",
      ZIP_INVALID_JSON: "problem.json 不是有效 JSON。",
      ZIP_PROBLEM_METADATA_INVALID: "problem.json 元数据不符合要求。",
      ZIP_STATEMENT_REQUIRED: "statement.md 不能为空。",
      ZIP_TEST_CASE_REQUIRED: "至少需要一组 .in / .out 测试用例。",
      ZIP_TEST_CASE_PAIR_MISMATCH: "测试用例的 .in 和 .out 文件没有成对出现。",
      ZIP_TEST_CASE_LIMIT_EXCEEDED: "测试用例数量超出限制。",
      PROBLEM_SLUG_ALREADY_EXISTS: "当前题目标识已存在，请修改 problem.json 中的 slug。",
      TOPIC_NOT_FOUND: "关联的知识点不存在或未发布。"
    };
    return messages[error.code] ?? error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "导入失败，请稍后重试。";
}

export function ProblemImportPage() {
  const router = useRouter();
  const { submit, loading } = useImportProblemZip();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!file) {
      setError("请选择一个 ZIP 文件。");
      return;
    }
    try {
      const result = await submit(file);
      const problem = result.data.problem;
      router.push(`/problems/${problem.id}`);
    } catch (err) {
      setError(getImportErrorMessage(err));
    }
  }

  return (
    <AppShell>
      <PageHeader
        actions={
          <Link
            className="rounded-md border border-[#bfdbfe] bg-white px-4 py-2 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href="/problems"
          >
            返回个人题库
          </Link>
        }
        description="上传安全格式的 ZIP 包，将题目描述和 .in / .out 测试用例导入到你的个人题库。"
        title="导入 ZIP 题目"
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <form
          className="rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <label className="block text-sm font-semibold text-[#0f172a]" htmlFor="zip-file">
            ZIP 文件
          </label>
          <input
            accept=".zip,application/zip,application/x-zip-compressed"
            className="mt-3 block w-full rounded-lg border border-[#bfdbfe] bg-white px-4 py-3 text-sm text-[#0f172a] outline-none file:mr-4 file:rounded-md file:border-0 file:bg-[#dbeafe] file:px-4 file:py-2 file:text-sm file:font-semibold file:text-[#1d4ed8] focus:ring-2 focus:ring-[#93c5fd]"
            id="zip-file"
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
              setError(null);
            }}
            type="file"
          />

          <div className="mt-5 rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-4 text-sm leading-6 text-[#475569]">
            <p className="font-semibold text-[#0f172a]">ZIP 包需要包含：</p>
            <ul className="mt-2 list-disc space-y-1 pl-5">
              <li>problem.json：题目标题、难度、可选 slug 和知识点</li>
              <li>statement.md：题面正文</li>
              <li>tests/01.in 与 tests/01.out：至少一组成对测试用例</li>
            </ul>
          </div>

          {error ? (
            <div className="mt-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
              {error.includes("登录") ? (
                <Link className="ml-2 font-semibold underline-offset-4 hover:underline" href="/login">
                  去登录
                </Link>
              ) : null}
            </div>
          ) : null}

          <button
            className="mt-6 rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 outline-none transition hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:opacity-60 focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            disabled={loading}
            type="submit"
          >
            {loading ? "正在导入..." : "导入到个人题库"}
          </button>
        </form>

        <aside className="rounded-xl border border-[#dbeafe] bg-white/80 p-6 text-sm leading-6 text-[#475569] shadow-sm shadow-blue-100/60">
          <h2 className="text-base font-semibold text-[#0f172a]">安全边界</h2>
          <p className="mt-3">
            Phase 9 只解析题目文本和测试用例文件，不执行上传内容，也不会运行评测或创建提交记录。
          </p>
          <div className="mt-5 space-y-3">
            <p>
              <span className="font-semibold text-[#0f172a]">大小限制：</span>ZIP 最大 10MB，单个文件最大 512KB。
            </p>
            <p>
              <span className="font-semibold text-[#0f172a]">文件类型：</span>仅允许 .json、.md、.in、.out。
            </p>
            <p>
              <span className="font-semibold text-[#0f172a]">版权提醒：</span>请只导入你有权使用的题面和测试数据。
            </p>
          </div>
        </aside>
      </div>
    </AppShell>
  );
}
