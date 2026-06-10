import Link from "next/link";

import { AppShell } from "@/components/AppShell";

const quickEntries = [
  {
    href: "/topics",
    title: "知识地图",
    description: "按照算法基础路线系统学习核心知识点，保留每个知识点的学习状态。"
  },
  {
    href: "/dashboard",
    title: "学习看板",
    description: "查看总体进度、最近学习、复习队列和下一步建议。"
  },
  {
    href: "/chat",
    title: "AI 问答",
    description: "围绕知识点进行启发式讲解，适合梳理概念和边界。"
  },
  {
    href: "/code-review",
    title: "代码诊断",
    description: "从算法思路、潜在错误、复杂度和修改建议分析代码。"
  },
  {
    href: "/problems/generate",
    title: "题目生成",
    description: "根据知识点和难度生成原创练习题，用于课后巩固。"
  }
];

export default function Home() {
  return (
    <AppShell>
      <section className="grid gap-8 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
        <div className="rounded-2xl border border-[#dbeafe] bg-white/80 p-6 shadow-sm shadow-blue-100/70 sm:p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.16em] text-[#2563eb]">
            MVP v0.1 学习工作台
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-[#0f172a] sm:text-5xl">
            AlgoMentor AI 算法学习助手
          </h1>
          <p className="mt-5 max-w-3xl text-lg leading-8 text-[#475569]">
            用知识地图、AI 辅导、代码诊断和学习看板，帮助你系统完成算法入门到进阶训练。
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href="/topics"
            >
              开始学习
            </Link>
            <Link
              className="rounded-md border border-[#bfdbfe] bg-white px-5 py-3 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
              href="/settings"
            >
              配置 AI 服务
            </Link>
          </div>
        </div>

        <aside className="rounded-2xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/70">
          <h2 className="text-xl font-semibold text-[#0f172a]">当前学习闭环</h2>
          <div className="mt-5 grid gap-3">
            {["知识地图", "AI 辅导", "代码诊断", "题目生成", "学习看板"].map((item, index) => (
              <div
                className="flex items-center gap-3 rounded-lg border border-[#e2e8f0] bg-[#f8fbff] px-4 py-3"
                key={item}
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#dbeafe] text-sm font-semibold text-[#1d4ed8]">
                  {index + 1}
                </span>
                <span className="font-semibold text-[#334155]">{item}</span>
              </div>
            ))}
          </div>
        </aside>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {quickEntries.map((item) => (
          <Link
            className="rounded-xl border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60 outline-none transition hover:-translate-y-0.5 hover:border-[#93c5fd] hover:shadow-md focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href={item.href}
            key={item.href}
          >
            <h3 className="text-lg font-semibold text-[#0f172a]">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-[#64748b]">{item.description}</p>
          </Link>
        ))}
      </section>

      <section className="mt-8 grid gap-4 rounded-xl border border-[#bfdbfe] bg-white/90 p-5 text-sm leading-7 text-[#475569] shadow-sm shadow-blue-100/60 lg:grid-cols-3">
        <p>
          <span className="font-semibold text-[#0f172a]">当前版本：</span>MVP v0.1
        </p>
        <p>
          <span className="font-semibold text-[#0f172a]">已完成：</span>
          知识地图 / AI 辅导 / 代码诊断 / 题目生成 / 学习看板
        </p>
        <p>
          <span className="font-semibold text-[#0f172a]">后续规划：</span>
          错题本 / 题库系统 / RAG 知识检索 / OJ 沙箱
        </p>
      </section>
    </AppShell>
  );
}
