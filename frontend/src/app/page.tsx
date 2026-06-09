import Link from "next/link";

const checks = [
  "Next.js 15 frontend skeleton",
  "FastAPI backend health endpoint",
  "Docker Compose service plan",
  "Phase 4 dashboard review loop"
];

const links = [
  { href: "/topics", label: "Open knowledge map" },
  { href: "/dashboard", label: "View dashboard" },
  { href: "/chat", label: "Ask AI tutor" },
  { href: "/code-review", label: "Review code" },
  { href: "/problems/generate", label: "Generate problem" }
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f7f4ee] text-[#1f2933]">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-12">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#50606f]">
          AlgoMentor AI
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
          Phase 4 learning dashboard is ready for review-focused practice.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-[#4a5563]">
          The platform now includes topic browsing, learning status updates,
          AI tutoring, code diagnosis, AI-generated practice prompts, and a
          rule-based dashboard for progress and next steps. Authentication and
          OJ features remain deferred.
        </p>

        <div className="mt-10 grid gap-3 sm:grid-cols-2">
          {checks.map((item) => (
            <div
              className="border border-[#d7d0c3] bg-white/70 px-4 py-3 text-sm font-medium shadow-sm"
              key={item}
            >
              {item}
            </div>
          ))}
        </div>

        <div className="mt-10 border-l-4 border-[#2f6f73] bg-white/80 px-5 py-4 text-sm text-[#40505f]">
          Backend health check:{" "}
          <code className="font-mono text-[#1d4f53]">
            http://localhost:8000/api/health
          </code>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          {links.map((item) => (
            <Link
              className="inline-flex w-fit bg-[#1f2933] px-5 py-3 text-sm font-semibold text-white"
              href={item.href}
              key={item.href}
            >
              {item.label}
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
