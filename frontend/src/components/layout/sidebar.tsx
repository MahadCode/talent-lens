"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  Briefcase,
  Users,
  FileSearch,
  MessagesSquare,
  Calendar,
  BarChart3,
  Settings,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";

import { BrandLogo } from "@/components/brand/logo";
import { cn } from "@/lib/utils/cn";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Jobs", href: "/jobs", icon: Briefcase },
  { label: "Candidates", href: "/candidates", icon: Users },
  { label: "Screening", href: "/resume-screening", icon: FileSearch },
  { label: "AI Interview", href: "/interviews", icon: MessagesSquare },
  { label: "Schedule", href: "/schedule", icon: Calendar },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "Settings", href: "/settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();

  React.useEffect(() => {
    NAV_ITEMS.forEach((item) => {
      router.prefetch(item.href);
    });
  }, [router]);

  return (
    <aside
      className={cn(
        "sticky top-0 hidden h-screen shrink-0 flex-col border-r border-heading/10 bg-surface lg:flex",
        collapsed ? "w-[76px]" : "w-[240px]",
      )}
    >
      <div className="flex h-[52px] items-center px-4">
        <BrandLogo markOnly={collapsed} />
      </div>

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
              <Link
                key={item.href}
                href={item.href}
                prefetch
                className={cn(
                "flex items-center gap-3 px-3 py-2.5 text-sm transition-colors",
                isActive ? "bg-heading/5 text-heading" : "text-muted-foreground hover:bg-heading/5 hover:text-heading",
              )}
            >
              <Icon className="h-[16px] w-[16px] shrink-0" />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-heading/10 p-3">
        <button
          onClick={onToggle}
          className="label-mono flex w-full items-center justify-center gap-2 px-3 py-2 text-muted-foreground hover:text-heading"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <ChevronsRight className="h-4 w-4" /> : <ChevronsLeft className="h-4 w-4" />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );
}
