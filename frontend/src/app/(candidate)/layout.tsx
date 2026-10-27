"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

import { CandidateShell } from "@/components/layout/candidate-shell";
import { useAuth } from "@/lib/hooks/use-auth";
import { isCandidate, isStaff } from "@/lib/auth/roles";
import { tokenStorage } from "@/lib/api/client";

export default function CandidateGroupLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user } = useAuth();

  React.useEffect(() => {
    if (!tokenStorage.getAccessToken()) {
      router.replace("/login");
    }
  }, [router]);

  React.useEffect(() => {
    if (user && isStaff(user) && !isCandidate(user)) {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (user && isStaff(user) && !isCandidate(user)) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Loader2 className="h-6 w-6 animate-spin text-heading" />
      </div>
    );
  }

  return <CandidateShell>{children}</CandidateShell>;
}
