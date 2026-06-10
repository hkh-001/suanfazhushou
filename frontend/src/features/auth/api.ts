import { apiFetch } from "@/lib/api/client";

import type { AuthLoginPayload, AuthRegisterPayload, AuthUserResponse, LogoutResponse } from "./types";

export function getCurrentUser(): Promise<AuthUserResponse> {
  return apiFetch<AuthUserResponse>("/auth/me");
}

export function register(payload: AuthRegisterPayload): Promise<AuthUserResponse> {
  return apiFetch<AuthUserResponse>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function login(payload: AuthLoginPayload): Promise<AuthUserResponse> {
  return apiFetch<AuthUserResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function logout(): Promise<LogoutResponse> {
  return apiFetch<LogoutResponse>("/auth/logout", {
    method: "POST"
  });
}
