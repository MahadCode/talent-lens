"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";

import { BrandLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api/auth";
import { getApiErrorMessage } from "@/lib/api/client";

function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";
  const presetEmail = searchParams.get("email") ?? "";
  const [email, setEmail] = React.useState(presetEmail);
  const [code, setCode] = React.useState("");
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [isResending, setIsResending] = React.useState(false);
  const [done, setDone] = React.useState(false);

  React.useEffect(() => {
    if (!token) return;
    let cancelled = false;
    setIsSubmitting(true);
    void authApi
      .verifyEmail({ token })
      .then(() => {
        if (cancelled) return;
        setDone(true);
        toast.success("Email verified. Sign in to continue.");
        router.replace("/login");
      })
      .catch((error) => {
        if (!cancelled) toast.error(getApiErrorMessage(error));
      })
      .finally(() => {
        if (!cancelled) setIsSubmitting(false);
      });
    return () => {
      cancelled = true;
    };
  }, [token, router]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      await authApi.verifyEmail({ email, code });
      toast.success("Email verified. Sign in to continue.");
      router.push("/login");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function onResend() {
    if (!email) {
      toast.error("Enter the email you registered with.");
      return;
    }
    setIsResending(true);
    try {
      await authApi.resendVerification(email);
      toast.success("If that inbox needs verification, a new code is on the way.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsResending(false);
    }
  }

  if (token && !done) {
    return <p className="text-sm text-muted-foreground">Confirming your email…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2 text-center lg:hidden">
        <BrandLogo />
      </div>
      <div className="space-y-1.5">
        <p className="label-mono text-muted-foreground">Verify</p>
        <h2 className="text-2xl font-normal tracking-tight text-heading">Check your email</h2>
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code we sent. Unverified accounts cannot use Talent Lens.
        </p>
      </div>
      <form onSubmit={(event) => void onSubmit(event)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="code">Code</Label>
          <Input
            id="code"
            inputMode="numeric"
            maxLength={6}
            placeholder="123456"
            value={code}
            onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
            required
          />
        </div>
        <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
          Verify email
        </Button>
      </form>
      <button type="button" className="label-mono w-full text-muted-foreground hover:text-heading" onClick={() => void onResend()} disabled={isResending}>
        {isResending ? "Sending…" : "Resend code"}
      </button>
      <p className="text-center text-sm text-muted-foreground">
        <Link href="/login" className="text-heading underline-offset-4 hover:underline">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <React.Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <VerifyEmailForm />
    </React.Suspense>
  );
}
