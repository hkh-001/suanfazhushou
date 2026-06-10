"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { ApiError } from "@/lib/api/client";

import { register } from "./api";

function friendlyRegisterError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === "EMAIL_ALREADY_REGISTERED") {
      return "该邮箱已经注册。";
    }
    if (error.code === "USERNAME_ALREADY_TAKEN") {
      return "该用户名已经被使用。";
    }
    if (error.code === "VALIDATION_ERROR") {
      return "请检查邮箱、用户名和密码格式。密码至少需要 8 位。";
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "注册失败，请稍后重试。";
}

export function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register({ email, username, password });
      router.push("/topics");
      router.refresh();
    } catch (err) {
      setError(friendlyRegisterError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell maxWidth="max-w-6xl">
      <PageHeader
        description="创建账号后，你的学习记录和看板数据会归属到当前用户。学习阶段和目标方向暂时使用默认配置。"
        title="注册"
      />
      <section className="mx-auto max-w-md rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
        <form className="grid gap-5" onSubmit={submit}>
          <label className="block text-sm font-medium text-[#334155]">
            邮箱
            <input
              autoComplete="email"
              className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              onChange={(event) => setEmail(event.target.value)}
              placeholder="user@example.com"
              required
              type="email"
              value={email}
            />
          </label>
          <label className="block text-sm font-medium text-[#334155]">
            用户名
            <input
              autoComplete="username"
              className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              maxLength={80}
              minLength={3}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="alice"
              required
              value={username}
            />
          </label>
          <label className="block text-sm font-medium text-[#334155]">
            密码
            <input
              autoComplete="new-password"
              className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              minLength={8}
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
            {loading ? "正在注册..." : "注册并开始学习"}
          </button>
          {error ? <p className="text-sm font-semibold text-red-700">{error}</p> : null}
        </form>
        <p className="mt-5 text-sm text-[#64748b]">
          已有账号？{" "}
          <Link className="font-semibold text-[#2563eb] underline-offset-4 hover:underline" href="/login">
            去登录
          </Link>
        </p>
      </section>
    </AppShell>
  );
}
