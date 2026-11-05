"use client";

import * as React from "react";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/auth/password-input";
import { authApi } from "@/lib/api/auth";
import { getApiErrorMessage } from "@/lib/api/client";
import { useAuth } from "@/lib/hooks/use-auth";

export function TwoFactorSettings() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [pending, setPending] = React.useState<"enable" | "disable" | null>(null);
  const [code, setCode] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [busy, setBusy] = React.useState(false);

  async function refreshUser() {
    await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
  }

  async function startEnable() {
    setBusy(true);
    try {
      await authApi.enable2fa();
      setPending("enable");
      toast.success("Check your email for a confirmation code.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function startDisable() {
    if (!password) {
      toast.error("Enter your current password first.");
      return;
    }
    setBusy(true);
    try {
      await authApi.disable2fa(password);
      setPending("disable");
      toast.success("Check your email for a confirmation code.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function confirm() {
    setBusy(true);
    try {
      if (pending === "enable") {
        await authApi.confirm2fa(code);
        toast.success("Two-step verification is on.");
      } else {
        await authApi.confirmDisable2fa(code);
        toast.success("Two-step verification is off.");
      }
      setPending(null);
      setCode("");
      setPassword("");
      await refreshUser();
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Two-step verification</CardTitle>
        <CardDescription>
          After your password, we email a 6-digit code. Only verified accounts can turn this on.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-muted-foreground">
          Status: {user?.two_factor_enabled ? "On" : "Off"}
          {user?.is_verified ? "" : " · verify your email first"}
        </p>
        {pending ? (
          <div className="space-y-3">
            <Label htmlFor="two-factor-code">Email code</Label>
            <Input
              id="two-factor-code"
              inputMode="numeric"
              maxLength={6}
              value={code}
              onChange={(event) => setCode(event.target.value.replace(/\D/g, "").slice(0, 6))}
            />
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setPending(null)}>
                Cancel
              </Button>
              <Button type="button" onClick={() => void confirm()} isLoading={busy}>
                Confirm
              </Button>
            </div>
          </div>
        ) : user?.two_factor_enabled ? (
          <div className="space-y-3">
            <Label htmlFor="disable-password">Current password</Label>
            <PasswordInput id="disable-password" value={password} onChange={(event) => setPassword(event.target.value)} />
            <div className="flex justify-end">
              <Button type="button" variant="outline" onClick={() => void startDisable()} isLoading={busy}>
                Turn off
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex justify-end">
            <Button type="button" onClick={() => void startEnable()} isLoading={busy} disabled={!user?.is_verified}>
              Turn on email codes
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
