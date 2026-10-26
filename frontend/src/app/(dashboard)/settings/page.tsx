"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { PasswordInput } from "@/components/auth/password-input";
import { TwoFactorSettings } from "@/components/auth/two-factor-settings";
import { useAuth } from "@/lib/hooks/use-auth";
import { authApi } from "@/lib/api/auth";
import { getApiErrorMessage } from "@/lib/api/client";
import { getInitials } from "@/lib/utils/cn";
import { useQueryClient } from "@tanstack/react-query";

interface ProfileFormValues {
  full_name: string;
  company_name: string;
}

interface PasswordFormValues {
  current_password: string;
  new_password: string;
}

export default function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [profileSubmitting, setProfileSubmitting] = React.useState(false);
  const [passwordSubmitting, setPasswordSubmitting] = React.useState(false);

  const profileForm = useForm<ProfileFormValues>({
    values: { full_name: user?.full_name ?? "", company_name: user?.company_name ?? "" },
  });
  const passwordForm = useForm<PasswordFormValues>();

  async function onProfileSubmit(values: ProfileFormValues) {
    setProfileSubmitting(true);
    try {
      await authApi.updateProfile(values);
      await queryClient.invalidateQueries({ queryKey: ["auth", "me"] });
      toast.success("Profile updated.");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setProfileSubmitting(false);
    }
  }

  async function onPasswordSubmit(values: PasswordFormValues) {
    setPasswordSubmitting(true);
    try {
      await authApi.changePassword(values.current_password, values.new_password);
      toast.success("Password changed. Please sign in again on other devices.");
      passwordForm.reset();
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setPasswordSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Account</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your profile, security, and preferences.</p>
      </div>

      <Tabs defaultValue="profile">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" id="profile">
          <Card>
            <CardHeader>
              <CardTitle>Profile</CardTitle>
              <CardDescription>This is how you appear across Talent Lens.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="flex items-center gap-4">
                <Avatar className="h-16 w-16">
                  {user?.profile_image ? <AvatarImage src={user.profile_image} alt={user.full_name} /> : null}
                  <AvatarFallback className="text-lg">{getInitials(user?.full_name)}</AvatarFallback>
                </Avatar>
                <Button variant="outline" size="sm">
                  Change photo
                </Button>
              </div>

              <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="full_name">Full name</Label>
                    <Input id="full_name" {...profileForm.register("full_name")} />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="company_name">Company</Label>
                    <Input id="company_name" {...profileForm.register("company_name")} />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Email</Label>
                  <Input value={user?.email ?? ""} disabled />
                </div>
                <div className="flex justify-end">
                  <Button type="submit" isLoading={profileSubmitting}>
                    Save changes
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="space-y-4">
          <TwoFactorSettings />
          <Card>
            <CardHeader>
              <CardTitle>Change password</CardTitle>
              <CardDescription>Choose a strong password you haven&apos;t used before.</CardDescription>
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
                <div className="flex justify-end">
                  <Button type="submit" isLoading={passwordSubmitting}>
                    Update password
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification preferences</CardTitle>
              <CardDescription>Choose what you want to be notified about.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                "Resume processed",
                "Candidate shortlisted",
                "Interview scheduled",
                "New applications",
                "AI recommendations",
              ].map((label) => (
                <label
                  key={label}
                  className="flex items-center justify-between rounded-xl border border-border px-4 py-3"
                >
                  <span className="text-sm text-heading">{label}</span>
                  <input type="checkbox" defaultChecked className="h-4 w-4 accent-primary" />
                </label>
              ))}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
