import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind class names, resolving conflicts (e.g. "p-2" vs "p-4")
 * in favor of the later class, and dropping falsy values.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/** Format a 0-100 score with a fixed single decimal, e.g. 82.5. */
export function formatScore(score: number): string {
  return score.toFixed(1);
}

/** Format an ISO date string as a short, readable date (e.g. "Jul 29, 2026"). */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

/** Format an ISO date string as a relative time (e.g. "3h ago", "2d ago"). */
export function formatRelativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return formatDate(iso);
}

/** Return initials (up to 2 letters) from a full name, for avatar fallbacks. */
export function getInitials(fullName: string | null | undefined): string {
  if (!fullName) return "?";
  const parts = fullName.trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1]?.[0] ?? "" : "";
  return (first + last).toUpperCase() || "?";
}
