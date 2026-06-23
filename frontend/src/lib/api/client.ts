const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
const API_TIMEOUT_MS = 15000;

export type ApiFetchInit = RequestInit & {
  timeoutMs?: number;
};

type ApiErrorBody = {
  error?: {
    code?: string;
    message?: string;
  };
};

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: ApiFetchInit): Promise<T> {
  const { timeoutMs = API_TIMEOUT_MS, ...requestInit } = init ?? {};
  const headers = new Headers(requestInit.headers);
  const isFormData =
    typeof FormData !== "undefined" && requestInit.body instanceof FormData;
  if (requestInit.body && !headers.has("Content-Type") && !isFormData) {
    headers.set("Content-Type", "application/json");
  }

  const controller = new AbortController();
  const externalSignal = requestInit.signal;
  const abortFromExternal = () => controller.abort();
  if (externalSignal?.aborted) {
    controller.abort();
  } else {
    externalSignal?.addEventListener("abort", abortFromExternal);
  }
  let timedOut = false;
  const timeoutId = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeoutMs);
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...requestInit,
      credentials: requestInit.credentials ?? "include",
      headers,
      signal: controller.signal
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      if (!timedOut) {
        throw new ApiError("请求已取消。", "REQUEST_ABORTED", 0);
      }
      throw new ApiError("请求超时，请确认后端服务和数据库是否正常运行。", "REQUEST_TIMEOUT", 0);
    }
    throw new ApiError("无法连接后端服务，请确认后端已启动。", "NETWORK_ERROR", 0);
  } finally {
    window.clearTimeout(timeoutId);
    externalSignal?.removeEventListener("abort", abortFromExternal);
  }

  if (!response.ok) {
    let body: ApiErrorBody = {};
    try {
      body = (await response.json()) as ApiErrorBody;
    } catch {
      body = {};
    }
    throw new ApiError(
      body.error?.message ?? "请求失败，请稍后重试。",
      body.error?.code ?? "REQUEST_FAILED",
      response.status
    );
  }

  return (await response.json()) as T;
}
