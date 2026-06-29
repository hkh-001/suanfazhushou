"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/AppShell";
import { PageHeader } from "@/components/PageHeader";
import { ApiError } from "@/lib/api/client";

import { clearAISettings, fetchAISettings, saveAISettings, testAISettings } from "./api";
import type { AISettingsStatus } from "./types";

const sourceLabels: Record<AISettingsStatus["source"], string> = {
  user: "当前账号配置",
  runtime: "全局运行时配置",
  persistent: "全局本地持久化配置",
  env: "环境变量配置",
  none: "当前未配置 AI 服务"
};

function friendlySettingsError(error: unknown) {
  if (error instanceof ApiError && error.code === "AUTH_REQUIRED") {
    return "请先登录后再配置个人 AI 服务。";
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
      setMessage("个人 AI 服务配置已保存。后端重启后会从数据库自动恢复。");
    } catch (err) {
      setError(friendlySettingsError(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleTest() {
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
    setClearing(true);
    setError(null);
    setMessage(null);
    try {
      const response = await clearAISettings();
      setStatus(response.data);
      setBaseUrl(response.data.base_url ?? "");
      setModel(response.data.model ?? "");
      setApiKey("");
      setMessage(
        response.data.source === "none"
          ? "你的个人 AI 配置已清除。当前没有可用的全局 fallback 配置。"
          : "你的个人 AI 配置已清除。当前会回退到全局配置。"
      );
    } catch (err) {
      setError(friendlySettingsError(err));
    } finally {
      setClearing(false);
    }
  }

  return (
    <AppShell maxWidth="max-w-6xl">
      <PageHeader
        description="为当前账号配置 OpenAI-compatible 大模型服务。保存后配置会写入后端数据库，服务重启后自动恢复。"
        title="个人 AI 服务配置"
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
          <div className="border-b border-[#e2e8f0] pb-5">
            <h2 className="text-xl font-semibold text-[#0f172a]">AI 服务配置</h2>
            <p className="mt-2 text-sm leading-6 text-[#64748b]">
              API 密钥只保存在后端数据库中，不会在页面明文显示，也不会写入浏览器存储。
            </p>
          </div>

          {loading ? <p className="mt-5 text-sm text-[#64748b]">正在加载配置状态...</p> : null}

          <form className="mt-6 grid gap-5" onSubmit={submit}>
            <label className="block text-sm font-medium text-[#334155]">
              接口地址
              <input
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] disabled:bg-slate-100"
                disabled={saving}
                onChange={(event) => setBaseUrl(event.target.value)}
                placeholder="https://api.openai.com/v1"
                value={baseUrl}
              />
            </label>
            <label className="block text-sm font-medium text-[#334155]">
              API 密钥
              <input
                className="mt-2 w-full rounded-md border border-[#bfdbfe] bg-white px-3 py-2 text-[#0f172a] outline-none focus:border-[#2563eb] focus:ring-2 focus:ring-[#bfdbfe] disabled:bg-slate-100"
                disabled={saving}
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
                disabled={saving}
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
                className="rounded-md bg-[#2563eb] px-5 py-3 text-sm font-semibold text-white outline-none transition hover:bg-[#1d4ed8] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:cursor-not-allowed disabled:bg-slate-300"
                disabled={saving}
                type="submit"
              >
                {saving ? "正在保存..." : "保存我的配置"}
              </button>
              <button
                className="rounded-md border border-[#bfdbfe] bg-white px-5 py-3 text-sm font-semibold text-[#1d4ed8] outline-none transition hover:bg-[#eff6ff] focus-visible:ring-2 focus-visible:ring-[#93c5fd] disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                disabled={testing}
                onClick={() => void handleTest()}
                type="button"
              >
                {testing ? "正在测试..." : "测试配置"}
              </button>
              <button
                className="rounded-md border border-red-200 bg-white px-5 py-3 text-sm font-semibold text-red-700 outline-none transition hover:bg-red-50 focus-visible:ring-2 focus-visible:ring-red-200 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
                disabled={clearing}
                onClick={() => void handleClear()}
                type="button"
              >
                {clearing ? "正在清除..." : "清除我的配置"}
              </button>
            </div>
          </form>

          {message ? <p className="mt-5 text-sm font-semibold text-[#1d4ed8]">{message}</p> : null}
          {error ? <p className="mt-5 text-sm font-semibold text-red-700">{error}</p> : null}
        </section>

        <aside className="space-y-4">
          <section className="rounded-xl border border-[#dbeafe] bg-white/95 p-5 shadow-sm shadow-blue-100/60">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <h2 className="text-xl font-semibold text-[#0f172a]">当前配置状态</h2>
              {status ? <StatusPill>{sourceLabels[status.source]}</StatusPill> : null}
            </div>

            {status ? (
              <dl className="mt-5 space-y-4 text-sm">
                <div>
                  <dt className="text-[#64748b]">配置状态</dt>
                  <dd className="mt-1 font-semibold text-[#0f172a]">
                    {status.configured ? "已配置" : "未配置"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#64748b]">接口地址</dt>
                  <dd className="mt-1 break-words font-semibold text-[#0f172a]">
                    {status.base_url ?? "未设置"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#64748b]">模型名称</dt>
                  <dd className="mt-1 break-words font-semibold text-[#0f172a]">
                    {status.model ?? "未设置"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#64748b]">API 密钥</dt>
                  <dd className="mt-1 font-semibold text-[#0f172a]">
                    {status.api_key_set ? "已设置" : "未设置"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#64748b]">全局运行时 fallback</dt>
                  <dd className="mt-1 font-semibold text-[#0f172a]">
                    {status.runtime_settings_enabled ? "可用" : "未启用"}
                  </dd>
                </div>
                <div>
                  <dt className="text-[#64748b]">全局本地文件 fallback</dt>
                  <dd className="mt-1 font-semibold text-[#0f172a]">
                    {status.persistent_settings_enabled ? "可用" : "未启用"}
                  </dd>
                </div>
              </dl>
            ) : (
              <p className="mt-4 text-sm text-[#64748b]">暂时无法读取配置状态。</p>
            )}
          </section>

          <section className="rounded-xl border border-[#dbeafe] bg-[#f8fbff] p-5 text-sm leading-6 text-[#475569] shadow-sm shadow-blue-100/60">
            <h2 className="text-lg font-semibold text-[#0f172a]">安全说明</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5">
              <li>当前账号配置优先于全局 fallback 配置。</li>
              <li>清除配置只会删除你的个人配置，不会影响其他用户。</li>
              <li>API 密钥不会在页面明文展示，也不会写入浏览器存储。</li>
              <li>当前版本将密钥保存在后端数据库中，生产环境需要进一步加密。</li>
            </ul>
          </section>
        </aside>
      </div>
    </AppShell>
  );
}
