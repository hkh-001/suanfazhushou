import Link from "next/link";

const checks = [
  "Next.js 15 frontend skeleton",
  "FastAPI backend health endpoint",
  "Docker Compose service plan",
  "Phase 2 knowledge map"
];

export default function Home() {
  return (
    <main className="min-h-screen bg-[#f7f4ee] text-[#1f2933]">
      <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col justify-center px-6 py-12">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-[#50606f]">
          AlgoMentor AI
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold leading-tight sm:text-5xl">
          Phase 2 knowledge map is ready for structured learning.
        </h1>
        <p className="mt-6 max-w-2xl text-lg leading-8 text-[#4a5563]">
          The platform now includes published topic browsing and learning status
          updates. AI workflows, authentication, and OJ features are deferred to
          later phases.
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

        <Link
          className="mt-6 inline-flex w-fit bg-[#1f2933] px-5 py-3 text-sm font-semibold text-white"
          href="/topics"
        >
          Open knowledge map
        </Link>
      </section>
    </main>
  );
}
