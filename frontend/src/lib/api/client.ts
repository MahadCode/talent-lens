import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ApiErrorBody, TokenPair } from "@/types/domain";

/**
 * Base URL for the FastAPI backend. Never hardcoded — read from the
 * environment so the same build can target dev/staging/prod backends.
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1";
const AUTH_CHANGED_EVENT = "talent-lens-auth";

function notifyAuthChanged() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event(AUTH_CHANGED_EVENT));
}

const ACCESS_TOKEN_KEY = "talent_lens_access_token";
const REFRESH_TOKEN_KEY = "talent_lens_refresh_token";

export const tokenStorage = {
  getAccessToken: (): string | null =>
    typeof window === "undefined" ? null : window.localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: (): string | null =>
    typeof window === "undefined" ? null : window.localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (tokens: TokenPair): void => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
    window.localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
    notifyAuthChanged();
  },
  clear: (): void => {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(ACCESS_TOKEN_KEY);
    window.localStorage.removeItem(REFRESH_TOKEN_KEY);
    notifyAuthChanged();
  },
};

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) {
    throw new Error("No refresh token available.");
  }
  const response = await axios.post<TokenPair>(`${API_BASE_URL}/auth/refresh`, {
    refresh_token: refreshToken,
  });
  tokenStorage.setTokens(response.data);
  return response.data.access_token;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config as (InternalAxiosRequestConfig & { _retry?: boolean }) | undefined;

    if (error.response?.status === 403 && error.response.data?.error === "email_not_verified") {
      tokenStorage.clear();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/verify-email")) {
        window.location.href = "/verify-email";
      }
      return Promise.reject(error);
    }

    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        refreshPromise ??= refreshAccessToken().finally(() => {
          refreshPromise = null;
        });
        const newAccessToken = await refreshPromise;
        originalRequest.headers.set("Authorization", `Bearer ${newAccessToken}`);
        return apiClient(originalRequest);
      } catch {
        tokenStorage.clear();
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  },
);

/** Extract a user-facing error message from any API error, with a safe fallback. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    if (!error.response) {
      return "Can't reach the server. Start the backend and try again.";
    }
    const body = error.response.data;
    const details = body?.details as { errors?: Array<{ msg?: string; loc?: unknown[] }> } | undefined;
    const fieldErrors = details?.errors
      ?.map((item) => item.msg)
      .filter(Boolean)
      .join(" ");
    if (fieldErrors) return fieldErrors;
    return body?.message ?? "Something went wrong. Please try again.";
  }
  return "Something went wrong. Please try again.";
}

export function getApiErrorCode(error: unknown): string | null {
  if (axios.isAxiosError<ApiErrorBody>(error)) {
    return error.response?.data?.error ?? null;
  }
  return null;
}

export { AUTH_CHANGED_EVENT };
