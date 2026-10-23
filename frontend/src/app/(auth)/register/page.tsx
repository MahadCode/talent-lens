"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { BrandLogo } from "@/components/brand/logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/auth/password-input";
import { PasswordStrength } from "@/components/auth/password-strength";
import { authApi } from "@/lib/api/auth";
import { getApiErrorMessage } from "@/lib/api/client";
import type { UserRole } from "@/types/domain";

const STAFF_ROLES: { value: UserRole; label: string }[] = [
  { value: "RECRUITER", label: "Recruiter" },
  { value: "HR_MANAGER", label: "HR Manager" },
  { value: "INTERVIEWER", label: "Interviewer" },
  { value: "ADMIN", label: "Admin" },
];

const registerSchema = z.object({
  full_name: z.string().min(1, "Full name is required."),
  email: z.string().email("Enter a valid email address."),
  company_name: z.string().optional(),
  role: z.enum(["ADMIN", "HR_MANAGER", "RECRUITER", "INTERVIEWER", "CANDIDATE"]),
  password: z.string().min(8, "Password must be at least 8 characters."),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

function RegisterForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const asCandidate = searchParams.get("as") === "candidate";
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [passwordValue, setPasswordValue] = React.useState("");
  const [formError, setFormError] = React.useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      company_name: "",
      password: "",
      role: asCandidate ? "CANDIDATE" : "RECRUITER",
    },
  });

  const selectedRole = watch("role");

  React.useEffect(() => {
    if (asCandidate) {
      setValue("role", "CANDIDATE");
    } else if (selectedRole === "CANDIDATE") {
      setValue("role", "RECRUITER");
    }
  }, [asCandidate, selectedRole, setValue]);

  async function onSubmit(values: RegisterFormValues) {
    setFormError(null);
    setIsSubmitting(true);
    try {
      const payload = {
        full_name: values.full_name.trim(),
        email: values.email.trim(),
        password: values.password,
        role: asCandidate ? ("CANDIDATE" as const) : values.role,
        company_name: asCandidate ? undefined : values.company_name?.trim() || undefined,
      };
      await authApi.register(payload);
      toast.success("Check your email to verify your account.");
      router.push(`/verify-email?email=${encodeURIComponent(payload.email)}`);
    } catch (error) {
      const message = getApiErrorMessage(error);
      setFormError(message);
      toast.error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col items-center gap-2 text-center lg:hidden">
        <BrandLogo />
      </div>

      <div className="space-y-1.5">
        <p className="label-mono text-muted-foreground">{asCandidate ? "Apply" : "Hire"}</p>
        <h2 className="text-2xl font-normal tracking-tight text-heading">Create your account</h2>
        <p className="text-sm text-muted-foreground">
          {asCandidate
            ? "Upload a resume and track your applications."
            : "Publish roles and review evidence-linked scores."}
        </p>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Link
          href="/register"
          className={`label-mono border px-3 py-2 text-center ${asCandidate ? "border-heading/15 text-muted-foreground" : "border-heading text-heading"}`}
        >
          I&apos;m hiring
        </Link>
        <Link
          href="/register?as=candidate"
          className={`label-mono border px-3 py-2 text-center ${asCandidate ? "border-heading text-heading" : "border-heading/15 text-muted-foreground"}`}
        >
          I&apos;m applying
        </Link>
      </div>

      <form method="post" noValidate onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {formError ? <p className="text-sm text-error">{formError}</p> : null}
        <div className="space-y-1.5">
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" placeholder="Jane Doe" {...register("full_name")} />
          {errors.full_name && <p className="text-xs text-error">{errors.full_name.message}</p>}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
          {errors.email && <p className="text-xs text-error">{errors.email.message}</p>}
        </div>

        {!asCandidate ? (
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1.5">
              <Label htmlFor="company_name">Company</Label>
              <Input id="company_name" placeholder="Northline Labs" {...register("company_name")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="role">Role</Label>
              <select
                id="role"
                className="flex h-10 w-full border border-border bg-surface px-3.5 py-2 text-sm text-heading"
                {...register("role")}
              >
                {STAFF_ROLES.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ) : null}

        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <PasswordInput
            id="password"
            {...register("password")}
            onChange={(event) => {
              setPasswordValue(event.target.value);
              void register("password").onChange(event);
            }}
          />
          <PasswordStrength password={passwordValue} />
          {errors.password && <p className="text-xs text-error">{errors.password.message}</p>}
        </div>

        <Button type="submit" className="w-full" size="lg" isLoading={isSubmitting}>
          ·· Create account
        </Button>
      </form>

      <p className="text-center text-sm text-muted-foreground">
        Already have an account?{" "}
        <Link href="/login" className="text-heading underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <React.Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <RegisterForm />
    </React.Suspense>
  );
}
