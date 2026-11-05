"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { ArrowLeft, MailCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api/auth";
import { getApiErrorMessage } from "@/lib/api/client";

const schema = z.object({ email: z.string().email("Enter a valid email address.") });
type FormValues = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [sent, setSent] = React.useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  async function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    try {
      await authApi.forgotPassword(values.email);
      setSent(true);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    } finally {
      setIsSubmitting(false);
    }
  }

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="space-y-4 text-center"
      >
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-success/10">
          <MailCheck className="h-6 w-6 text-success" />
        </div>
        <h2 className="text-xl font-semibold text-heading">Check your email</h2>
        <p className="text-sm text-muted-foreground">
          If that email is registered, we&apos;ve sent a link to reset your password.
        </p>
        <Link href="/login" className="inline-flex items-center gap-1.5 text-sm font-medium text-primary hover:underline">
          <ArrowLeft className="h-3.5 w-3.5" /> Back to sign in
        </Link>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1.5">
        <h2 className="text-2xl font-semibold tracking-tight text-heading">Forgot your password?</h2>
        <p className="text-sm text-muted-foreground">
          Enter your email and we&apos;ll send you a link to reset it.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
          {errors.email && <p className="text-xs text-error">{errors.email.message}</p>}
        </div>

        <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
          Send reset link
        </Button>
      </form>

      <Link
        href="/login"
        className="flex items-center justify-center gap-1.5 text-sm font-medium text-primary hover:underline"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to sign in
      </Link>
    </div>
  );
}
