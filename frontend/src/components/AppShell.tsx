"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

import { useCurrentUser } from "@/features/auth/hooks";

const navItems = [
  { href: "/topics", label: "知识地图" },
  { href: "/dashboard", label: "学习看板" },
  { href: "/chat", label: "AI 问答" },
  { href: "/code-review", label: "代码诊断" },
  { href: "/problems/generate", label: "题目生成" },
  { href: "/settings", label: "设置" }
];

function isActive(pathname: string, href: string) {
  if (href === "/topics") {
    return pathname === "/topics" || pathname.startsWith("/topics/");
  }
  return pathname === href;
}

export function AppShell({
  children,
  maxWidth = "max-w-7xl"
}: {
  children: ReactNode;
  maxWidth?: "max-w-6xl" | "max-w-7xl";
}) {
  const pathname = usePathname();
  const { user, loading, signOut } = useCurrentUser();

  return (
    <main className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50 to-white text-[#0f172a]">
      <header className="sticky top-0 z-20 border-b border-blue-100/80 bg-white/85 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <Link
            className="group flex flex-col rounded-md outline-none focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
            href="/"
          >
            <span className="text-base font-semibold text-[#0f172a] transition group-hover:text-[#1d4ed8]">
              AlgoMentor AI
            </span>
            <span className="text-xs font-medium text-[#2563eb]">算法学习助手</span>
          </Link>

          <div className="flex flex-wrap items-center justify-end gap-2">
            <nav aria-label="主导航" className="flex flex-wrap items-center gap-1 text-sm">
              {navItems.map((item) => {
                const active = isActive(pathname, item.href);
                return (
                  <Link
                    aria-current={active ? "page" : undefined}
                    className={`rounded-md px-3 py-2 font-semibold outline-none transition focus-visible:ring-2 focus-visible:ring-[#93c5fd] ${
                      active
                        ? "bg-[#2563eb] text-white shadow-sm shadow-blue-200"
                        : "text-[#334155] hover:bg-[#eff6ff] hover:text-[#1d4ed8]"
                    }`}
                    href={item.href}
                    key={item.href}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center gap-2 border-l border-[#dbeafe] pl-2 text-sm">
              {loading ? (
                <span className="rounded-md px-3 py-2 text-[#64748b]">检查登录状态...</span>
              ) : user ? (
                <>
                  <span className="rounded-md bg-[#eff6ff] px-3 py-2 font-semibold text-[#1d4ed8]">
                    {user.is_dev_user ? "开发用户" : user.username}
                  </span>
                  {!user.is_dev_user ? (
                    <button
                      className="rounded-md border border-[#bfdbfe] bg-white px-3 py-2 font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                      onClick={() => void signOut()}
                      type="button"
                    >
                      退出
                    </button>
                  ) : null}
                </>
              ) : (
                <>
                  <Link
                    className="rounded-md px-3 py-2 font-semibold text-[#334155] outline-none transition hover:bg-[#eff6ff] hover:text-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                    href="/login"
                  >
                    登录
                  </Link>
                  <Link
                    className="rounded-md bg-[#2563eb] px-3 py-2 font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd]"
                    href="/register"
                  >
                    注册
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      <div className={`mx-auto w-full ${maxWidth} px-4 py-8 sm:px-6 lg:px-8`}>{children}</div>
    </main>
  );
}
