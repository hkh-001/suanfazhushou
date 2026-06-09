import Link from "next/link";

const navItems = [
  { href: "/topics", label: "知识地图" },
  { href: "/dashboard", label: "学习看板" },
  { href: "/chat", label: "AI 问答" },
  { href: "/code-review", label: "代码诊断" },
  { href: "/problems/generate", label: "题目生成" },
  { href: "/settings", label: "设置" }
];

const features = [
  {
    href: "/topics",
    title: "知识地图",
    description: "按主题系统学习算法基础，保留学习状态与知识点内容。"
  },
  {
    href: "/dashboard",
    title: "学习看板",
    description: "汇总进度、最近学习、复习队列和下一步建议。"
  },
  {
    href: "/chat",
    title: "AI 问答",
    description: "围绕知识点进行启发式讲解，适合梳理概念和边界。"
  },
  {
    href: "/code-review",
    title: "代码诊断",
    description: "从 bug、复杂度和修改建议几个角度分析代码。"
  },
  {
    href: "/problems/generate",
    title: "题目生成",
    description: "根据知识点和难度生成原创练习题，用于课后巩固。"
  }
];

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50 to-white text-[#0f172a]">
      <section className="mx-auto w-full max-w-7xl px-6 py-6">
        <nav className="flex flex-wrap items-center justify-between gap-4 rounded-lg border border-[#dbeafe] bg-white/85 px-4 py-3 shadow-sm shadow-blue-100/60">
          <Link className="flex flex-col" href="/">
            <span className="text-base font-semibold text-[#0f172a]">AlgoMentor AI</span>
            <span className="text-xs font-medium text-[#2563eb]">算法学习助手</span>
          </Link>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {navItems.map((item) => (
              <Link
                className="rounded-md px-3 py-2 font-semibold text-[#334155] transition hover:bg-[#eff6ff] hover:text-[#1d4ed8]"
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </nav>

        <div className="grid min-h-[calc(100vh-96px)] items-center gap-10 py-12 lg:grid-cols-[1.05fr_0.95fr]">
          <section>
            <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2563eb]">
              MVP v0.1
            </p>
            <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
              AlgoMentor AI 算法学习助手
            </h1>
            <p className="mt-6 max-w-3xl text-lg leading-8 text-[#475569]">
              用知识地图、AI 辅导、代码诊断和学习看板，帮助你系统完成算法入门到进阶训练。
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white shadow-sm shadow-blue-200 transition hover:bg-[#1d4ed8]"
                href="/topics"
              >
                开始学习
              </Link>
              <Link
                className="rounded-md border border-[#bfdbfe] bg-white px-5 py-3 text-sm font-semibold text-[#1d4ed8] transition hover:bg-[#eff6ff]"
                href="/settings"
              >
                配置 AI 服务
              </Link>
            </div>
          </section>

          <aside className="rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-lg shadow-blue-100/70">
            <h2 className="text-xl font-semibold">学习闭环</h2>
            <div className="mt-5 grid gap-3">
              {features.map((item, index) => (
                <Link
                  className="group rounded-lg border border-[#e2e8f0] bg-[#f8fbff] p-4 transition hover:border-[#93c5fd] hover:bg-white"
                  href={item.href}
                  key={item.href}
                >
                  <div className="flex items-start gap-3">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#dbeafe] text-sm font-semibold text-[#1d4ed8] group-hover:bg-[#2563eb] group-hover:text-white">
                      {index + 1}
                    </span>
                    <div>
                      <h3 className="font-semibold text-[#0f172a]">{item.title}</h3>
                      <p className="mt-1 text-sm leading-6 text-[#64748b]">{item.description}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </aside>
        </div>

        <section className="mb-10 rounded-lg border border-[#bfdbfe] bg-white/90 px-5 py-4 text-sm leading-7 text-[#475569] shadow-sm">
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
      </section>
    </main>
  );
}
