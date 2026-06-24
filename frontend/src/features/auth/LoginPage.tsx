"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { ApiError } from "@/lib/api/client";

import { login } from "./api";

function friendlyLoginError(error: unknown) {
  if (error instanceof ApiError && error.code === "INVALID_CREDENTIALS") {
    return "学号或密码不正确。";
  }
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "登录失败，请稍后重试。";
}

export function LoginPage() {
  const router = useRouter();
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login({ student_id: studentId.trim(), password });
      router.push("/dashboard");
      router.refresh();
    } catch (err) {
      setError(friendlyLoginError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell maxWidth="max-w-6xl">
      <PageHeader description="使用账号登录后，你的学习记录、看板数据和后续个人内容会归属到当前用户。" title="登录" />
      <section className="mx-auto max-w-md rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
        <form className="grid gap-5" onSubmit={submit}>
          <label className="block text-sm font-medium text-[#334155]">
            学号
            <input
              autoComplete="username"
              className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              onChange={(event) => setStudentId(event.target.value)}
              placeholder="20240001"
              required
              value={studentId}
            />
          </label>
          <label className="block text-sm font-medium text-[#334155]">
            密码
            <input
              autoComplete="current-password"
              className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          <button
            className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            {loading ? "正在登录..." : "登录"}
          </button>
          {error ? <p className="text-sm font-semibold text-red-700">{error}</p> : null}
        </form>
        <p className="mt-5 text-sm text-[#64748b]">
          还没有账号？{" "}
          <Link className="font-semibold text-[#2563eb] underline-offset-4 hover:underline" href="/register">
            去注册
          </Link>
        </p>
      </section>
    </AppShell>
  );
}
