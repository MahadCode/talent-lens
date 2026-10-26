"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Briefcase, FileText, FolderOpen, Settings } from "lucide-react";

import { BrandLogo } from "@/components/brand/logo";
import { useAuth } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils/cn";

const NAV = [
  { label: "Open jobs", href: "/app", icon: Briefcase },
  { label: "Applications", href: "/app/applications", icon: FolderOpen },
  { label: "Resume", href: "/app/resume", icon: FileText },
  { label: "Settings", href: "/app/settings", icon: Settings },
];

export function CandidateShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  React.useEffect(() => {
    NAV.forEach((item) => {
      router.prefetch(item.href);
    });
  }, [router]);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-30 flex h-[52px] items-center justify-between border-b border-heading/10 bg-surface px-4 sm:px-8">
        <BrandLogo />
        <nav className="hidden items-center gap-1 md:flex">
          {NAV.map((item) => {
            const active = pathname === item.href || (item.href !== "/app" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                prefetch
                className={cn(
                  "label-mono px-3 py-2",
                  active ? "text-heading" : "text-muted-foreground hover:text-heading",
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-3">
          <span className="hidden text-sm text-muted-foreground sm:inline">{user?.full_name}</span>
          <button type="button" onClick={() => void logout()} className="label-mono text-muted-foreground hover:text-heading">
            Log out
          </button>
        </div>
      </header>
      <main className="mx-auto w-full max-w-[1100px] px-4 py-8 pb-24 sm:px-8 md:pb-8">{children}</main>
      <nav className="fixed inset-x-0 bottom-0 z-30 flex items-center justify-around border-t border-heading/10 bg-surface px-2 py-2 md:hidden">
        {NAV.map((item) => {
          const active = pathname === item.href || (item.href !== "/app" && pathname.startsWith(item.href));
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              prefetch
              className={cn("label-mono flex flex-col items-center gap-1 px-2 py-1", active ? "text-heading" : "text-muted-foreground")}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
