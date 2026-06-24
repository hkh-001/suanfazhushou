"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { ApiError } from "@/lib/api/client";

import { register } from "./api";
import type { AuthRegisterPayload } from "./types";

const levelOptions: Array<{ value: AuthRegisterPayload["current_level"]; label: string }> = [
  { value: "beginner", label: "0 基础" },
  { value: "elementary", label: "入门" },
  { value: "popularization", label: "普及" },
  { value: "improvement", label: "提高" }
];

const goalOptions: Array<{ value: AuthRegisterPayload["goal_track"]; label: string }> = [
  { value: "course", label: "提高基础课程成绩" },
  { value: "lanqiao", label: "蓝桥杯获奖" },
  { value: "icpc", label: "参加 ICPC/CCPC" },
  { value: "self_study", label: "自学提升" }
];

function friendlyRegisterError(error: unknown) {
  if (error instanceof ApiError) {
    if (error.code === "STUDENT_ID_ALREADY_EXISTS") {
      return "该学号已经注册。";
    }
    if (error.code === "VALIDATION_ERROR") {
      return "请检查学号、显示名称、画像选项和密码格式。密码至少需要 8 位。";
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
  const [studentId, setStudentId] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [currentLevel, setCurrentLevel] = useState<AuthRegisterPayload["current_level"]>("beginner");
  const [goalTrack, setGoalTrack] = useState<AuthRegisterPayload["goal_track"]>("course");
  const [goalDescription, setGoalDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await register({
        student_id: studentId.trim(),
        password,
        name: name.trim(),
        current_level: currentLevel,
        goal_track: goalTrack,
        goal_description: goalDescription || null
      });
      router.push("/dashboard");
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
        description="创建学生账号并填写初始画像，后续 AI 辅导、题目生成和学习建议会参考你的基础水平与目标。"
        title="注册"
      />
      <section className="mx-auto max-w-2xl rounded-xl border border-[#dbeafe] bg-white/95 p-6 shadow-sm shadow-blue-100/60">
        <form className="grid gap-5" onSubmit={submit}>
          <div className="grid gap-5 md:grid-cols-2">
            <label className="block text-sm font-medium text-[#334155]">
              学号
              <input
                autoComplete="username"
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
                maxLength={80}
                minLength={2}
                onChange={(event) => setStudentId(event.target.value)}
                placeholder="20240001"
                required
                value={studentId}
              />
            </label>
            <label className="block text-sm font-medium text-[#334155]">
              显示名称
              <input
                autoComplete="name"
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
                maxLength={40}
                minLength={2}
                onChange={(event) => setName(event.target.value)}
                placeholder="张三"
                required
                value={name}
              />
            </label>
          </div>

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

          <div className="grid gap-5 md:grid-cols-2">
            <label className="block text-sm font-medium text-[#334155]">
              当前水平
              <select
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
                onChange={(event) => setCurrentLevel(event.target.value as AuthRegisterPayload["current_level"])}
                value={currentLevel}
              >
                {levelOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="block text-sm font-medium text-[#334155]">
              学习目标
              <select
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
                onChange={(event) => setGoalTrack(event.target.value as AuthRegisterPayload["goal_track"])}
                value={goalTrack}
              >
                {goalOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="block text-sm font-medium text-[#334155]">
            目标补充说明（可选）
            <textarea
              className="mt-2 min-h-28 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe]"
              maxLength={500}
              onChange={(event) => setGoalDescription(event.target.value)}
              placeholder="例如：希望本学期高级语言程序设计达到 90 分，或者一年内准备蓝桥杯省赛。"
              value={goalDescription}
            />
          </label>

          <button
            className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:opacity-60"
            disabled={loading}
            type="submit"
          >
            {loading ? "正在注册..." : "注册并进入学习看板"}
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
