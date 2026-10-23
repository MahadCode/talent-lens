import { apiClient, tokenStorage } from "@/lib/api/client";
import type { LoginResult, RegisterResult, TokenPair, User, UserRole } from "@/types/domain";

export interface RegisterPayload {
  full_name: string;
  email: string;
  password: string;
  role: UserRole;
  company_name?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

/** Service layer for authentication endpoints (`/auth/*`). */
export const authApi = {
  async register(payload: RegisterPayload): Promise<RegisterResult> {
    const { data } = await apiClient.post<RegisterResult>("/auth/register", payload);
    return data;
  },

  async login(payload: LoginPayload): Promise<LoginResult> {
    const { data } = await apiClient.post<LoginResult>("/auth/login", payload);
    if (data.access_token && data.refresh_token) {
      tokenStorage.setTokens({
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        token_type: data.token_type ?? "bearer",
      });
    }
    return data;
  },

  async login2fa(challengeId: string, code: string): Promise<TokenPair> {
    const { data } = await apiClient.post<TokenPair>("/auth/login/2fa", {
      challenge_id: challengeId,
      code,
    });
    tokenStorage.setTokens(data);
    return data;
  },

  async verifyEmail(payload: { token?: string; email?: string; code?: string }): Promise<void> {
    await apiClient.post("/auth/verify-email", payload);
  },

  async resendVerification(email: string): Promise<void> {
    await apiClient.post("/auth/resend-verification", { email });
  },

  async enable2fa(): Promise<void> {
    await apiClient.post("/auth/2fa/enable");
  },

  async confirm2fa(code: string): Promise<User> {
    const { data } = await apiClient.post<User>("/auth/2fa/confirm", { code });
    return data;
  },

  async disable2fa(password: string): Promise<void> {
    await apiClient.post("/auth/2fa/disable", { password });
  },

  async confirmDisable2fa(code: string): Promise<User> {
    const { data } = await apiClient.post<User>("/auth/2fa/disable/confirm", { code });
    return data;
  },

  async logout(): Promise<void> {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      await apiClient.post("/auth/logout", { refresh_token: refreshToken }).catch(() => undefined);
    }
    tokenStorage.clear();
  },

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post("/auth/forgot-password", { email });
  },

  async resetPassword(resetToken: string, newPassword: string): Promise<void> {
    await apiClient.post("/auth/reset-password", { reset_token: resetToken, new_password: newPassword });
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post("/auth/change-password", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  async me(): Promise<User> {
    const { data } = await apiClient.get<User>("/auth/me");
    return data;
  },

  async updateProfile(payload: { full_name?: string; company_name?: string }): Promise<User> {
    const { data } = await apiClient.put<User>("/auth/profile", payload);
    return data;
  },
};
