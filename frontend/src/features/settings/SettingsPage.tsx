"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";

import { clearAISettings, fetchAISettings, saveAISettings, testAISettings } from "./api";
import type { AISettingsStatus } from "./types";

const sourceLabels: Record<AISettingsStatus["source"], string> = {
  runtime: "当前使用运行时配置",
  env: "当前使用环境变量配置",
  none: "当前未配置 AI 服务"
};

function friendlySettingsError(error: unknown) {
  if (error instanceof ApiError && error.code === "FEATURE_DISABLED") {
    return "运行时 AI 设置当前未启用。如需本地演示，请设置 ENABLE_RUNTIME_AI_SETTINGS=true。";
  }
  if (error instanceof ApiError || error instanceof Error) {
    return error.message;
  }
  return "请求失败，请稍后重试。";
}

function StatusPill({ children }: { children: string }) {
  return (
    <span className="inline-flex rounded-full border border-[#bfdbfe] bg-[#eff6ff] px-3 py-1 text-xs font-semibold text-[#1d4ed8]">
      {children}
    </span>
  );
}

export function SettingsPage() {
  const [status, setStatus] = useState<AISettingsStatus | null>(null);
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runtimeEnabled = status?.runtime_settings_enabled ?? false;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetchAISettings();
      setStatus(response.data);
      setBaseUrl(response.data.base_url ?? "");
      setModel(response.data.model ?? "");
    } catch (err) {
      setError(friendlySettingsError(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!runtimeEnabled) {
      setError("运行时 AI 设置当前未启用。如需本地演示，请设置 ENABLE_RUNTIME_AI_SETTINGS=true。");
      return;
    }
    setSaving(true);
    setError(null);
    setMessage(null);
    try {
      const response = await saveAISettings({
        base_url: baseUrl,
        api_key: apiKey,
        model
      });
      setStatus(response.data);
      setBaseUrl(response.data.base_url ?? "");
      setModel(response.data.model ?? "");
      setApiKey("");
      setMessage("AI 服务配置已保存到后端运行时内存。");
    } catch (err) {
      setError(friendlySettingsError(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
    if (!runtimeEnabled) {
      setError("运行时 AI 设置当前未启用。如需本地演示，请设置 ENABLE_RUNTIME_AI_SETTINGS=true。");
      return;
    }
    setTesting(true);
    setError(null);
    setMessage(null);
    try {
      await testAISettings();
      setMessage("AI 服务测试通过。");
    } catch (err) {
      setError(friendlySettingsError(err));
    } finally {
      setTesting(false);
    }
  }

  async function handleClear() {
    if (!runtimeEnabled) {
      setError("运行时 AI 设置当前未启用。如需本地演示，请设置 ENABLE_RUNTIME_AI_SETTINGS=true。");
      return;
    }
    setClearing(true);
    setError(null);
    setMessage(null);
    try {
      const response = await clearAISettings();
      setStatus(response.data);
      setBaseUrl(response.data.base_url ?? "");
      setModel(response.data.model ?? "");
      setApiKey("");
      setMessage("运行时 AI 配置已清除。");
    } catch (err) {
      setError(friendlySettingsError(err));
    } finally {
      setClearing(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-sky-50 via-blue-50 to-white text-[#0f172a]">
      <section className="mx-auto max-w-5xl px-6 py-10">
        <nav className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <Link className="text-sm font-semibold text-[#2563eb]" href="/">
            返回首页
          </Link>
          <div className="flex flex-wrap gap-3 text-sm">
            <Link className="font-semibold text-[#1d4ed8]" href="/topics">
              知识地图
            </Link>
            <Link className="font-semibold text-[#1d4ed8]" href="/chat">
              AI 问答
            </Link>
          </div>
        </nav>

        <header>
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-[#2563eb]">
            SETTINGS
          </p>
          <h1 className="mt-3 text-4xl font-semibold">系统设置</h1>
          <p className="mt-4 max-w-3xl leading-7 text-[#475569]">
            配置本地开发或演示环境中的 OpenAI-compatible 大模型服务。配置只保存在后端运行时内存中，
            服务重启后需要重新配置。
          </p>
        </header>

        <section className="mt-8 rounded-lg border border-[#dbeafe] bg-white/90 p-5 shadow-sm shadow-blue-100/60">
          <div className="flex flex-wrap items-start justify-between gap-4 border-b border-[#e2e8f0] pb-5">
            <div>
              <h2 className="text-xl font-semibold">AI 服务配置</h2>
              <p className="mt-2 text-sm leading-6 text-[#64748b]">
                请不要在公共环境中输入真实密钥。API 密钥不会显示明文，也不会写入浏览器存储。
              </p>
            </div>
            {status ? <StatusPill>{sourceLabels[status.source]}</StatusPill> : null}
          </div>

          {loading ? <p className="mt-5 text-sm text-[#64748b]">正在加载配置状态...</p> : null}

          {status ? (
            <div className="mt-5 grid gap-4 rounded-lg border border-[#dbeafe] bg-[#f8fbff] p-4 text-sm text-[#475569] md:grid-cols-2">
              <p>
                <span className="font-semibold text-[#0f172a]">运行时修改：</span>
                {status.runtime_settings_enabled ? "已启用" : "未启用"}
              </p>
              <p>
                <span className="font-semibold text-[#0f172a]">配置状态：</span>
                {status.configured ? "已配置" : "未配置"}
              </p>
              <p>
                <span className="font-semibold text-[#0f172a]">接口地址：</span>
                {status.base_url ?? "未设置"}
              </p>
              <p>
                <span className="font-semibold text-[#0f172a]">模型名称：</span>
                {status.model ?? "未设置"}
              </p>
              <p>
                <span className="font-semibold text-[#0f172a]">API 密钥：</span>
                {status.api_key_set ? "已设置" : "未设置"}
              </p>
            </div>
          ) : null}

          {!runtimeEnabled ? (
            <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm leading-6 text-amber-900">
              运行时 AI 设置当前未启用。如需本地演示，请设置{" "}
              <code className="font-mono">ENABLE_RUNTIME_AI_SETTINGS=true</code> 后重启后端。
            </div>
          ) : null}

          <form className="mt-6 grid gap-5" onSubmit={submit}>
            <label className="block text-sm font-medium text-[#334155]">
              接口地址
              <input
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] disabled:bg-slate-100"
                disabled={!runtimeEnabled || saving}
                onChange={(event) => setBaseUrl(event.target.value)}
                placeholder="https://api.openai.com/v1"
                value={baseUrl}
              />
            </label>
            <label className="block text-sm font-medium text-[#334155]">
              API 密钥
              <input
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] disabled:bg-slate-100"
                disabled={!runtimeEnabled || saving}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="sk-..."
                type="password"
                value={apiKey}
              />
            </label>
            <label className="block text-sm font-medium text-[#334155]">
              模型名称
              <input
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] disabled:bg-slate-100"
                disabled={!runtimeEnabled || saving}
                onChange={(event) => setModel(event.target.value)}
                placeholder="gpt-4o-mini / deepseek-chat / kimi-k2"
                value={model}
              />
            </label>

            <p className="text-sm leading-6 text-[#64748b]">
              “测试配置”会真实调用一次模型接口，可能产生少量模型调用费用。
            </p>

            <div className="flex flex-wrap gap-3">
              <button
                className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#1d4ed8] disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={!runtimeEnabled || saving}
                type="submit"
              >
                {saving ? "正在保存..." : "保存配置"}
              </button>
              <button
                className="rounded-md border border-[#bfdbfe] bg-white px-5 py-3 text-sm font-semibold text-[#1d4ed8] transition hover:bg-[#eff6ff] disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                disabled={!runtimeEnabled || testing}
                onClick={() => void handleTest()}
                type="button"
              >
                {testing ? "正在测试..." : "测试配置"}
              </button>
              <button
                className="rounded-md border border-red-200 bg-white px-5 py-3 text-sm font-semibold text-red-700 transition hover:bg-red-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                disabled={!runtimeEnabled || clearing}
                onClick={() => void handleClear()}
                type="button"
              >
                {clearing ? "正在清除..." : "清除配置"}
              </button>
            </div>
          </form>

          {message ? <p className="mt-5 text-sm font-semibold text-[#1d4ed8]">{message}</p> : null}
          {error ? <p className="mt-5 text-sm font-semibold text-red-700">{error}</p> : null}
        </section>
      </section>
    </main>
  );
}
