"use client";

import { cn } from "@/lib/utils/cn";

function getStrength(password: string): { score: number; label: string } {
  let score = 0;
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const labels = ["Very weak", "Weak", "Fair", "Good", "Strong"];
  return { score, label: labels[Math.min(score, labels.length - 1)] ?? "Very weak" };
}

/** Visual password strength meter, purely client-side heuristic. */
export function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;
  const { score, label } = getStrength(password);
  const colors = ["bg-error", "bg-error", "bg-warning", "bg-secondary", "bg-success"];

  return (
    <div className="mt-2 space-y-1.5">
      <div className="flex gap-1">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className={cn("h-1 flex-1 rounded-full transition-colors", i < score ? colors[score - 1] : "bg-muted")}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}
