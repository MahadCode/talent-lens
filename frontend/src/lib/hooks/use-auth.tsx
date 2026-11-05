"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { authApi } from "@/lib/api/auth";
import { AUTH_CHANGED_EVENT, tokenStorage } from "@/lib/api/client";
import { homeForRole } from "@/lib/auth/roles";
import type { User } from "@/types/domain";

interface AuthContextValue {
  user: User | undefined;
  isLoading: boolean;
  isAuthenticated: boolean;
  homePath: string;
  logout: () => Promise<void>;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [hasToken, setHasToken] = React.useState(false);

  React.useEffect(() => {
    const sync = () => setHasToken(Boolean(tokenStorage.getAccessToken()));
    sync();
    window.addEventListener(AUTH_CHANGED_EVENT, sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener(AUTH_CHANGED_EVENT, sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  const { data: user, isLoading } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    enabled: hasToken,
    retry: false,
  });

  const logout = React.useCallback(async () => {
    await authApi.logout();
    queryClient.clear();
    router.push("/login");
  }, [queryClient, router]);

  const homePath = homeForRole(user?.role);

  const value: AuthContextValue = {
    user,
    isLoading: hasToken && isLoading,
    isAuthenticated: Boolean(user),
    homePath,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider.");
  return ctx;
}
