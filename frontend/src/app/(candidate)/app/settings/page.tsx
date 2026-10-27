"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { TwoFactorSettings } from "@/components/auth/two-factor-settings";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { PasswordInput } from "@/components/auth/password-input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api/auth";
import { getApiErrorMessage } from "@/lib/api/client";

interface PasswordFormValues {
  current_password: string;
  new_password: string;
}

export default function CandidateSettingsPage() {
  const passwordForm = useForm<PasswordFormValues>();
  const [passwordSubmitting, setPasswordSubmitting] = React.useState(false);

  async function onPasswordSubmit(values: PasswordFormValues) {
    setPasswordSubmitting(true);
    try {
      await authApi.changePassword(values.current_password, values.new_password);
      toast.success("Password changed.");
      passwordForm.reset();
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setPasswordSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Account</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight">Settings</h1>
      </div>
      <TwoFactorSettings />
      <Card>
        <CardHeader>
          <CardTitle>Change password</CardTitle>
          <CardDescription>This signs other devices out.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="current_password">Current password</Label>
              <PasswordInput id="current_password" {...passwordForm.register("current_password")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="new_password">New password</Label>
              <PasswordInput id="new_password" {...passwordForm.register("new_password")} />
            </div>
            <Button type="submit" isLoading={passwordSubmitting}>
              Update password
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
