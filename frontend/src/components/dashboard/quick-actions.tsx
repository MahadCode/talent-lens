"use client";

import Link from "next/link";
import { Plus, FileUp, MessagesSquare, BarChart3 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const ACTIONS = [
  { label: "New Job", href: "/jobs/new", icon: Plus },
  { label: "Upload Resume", href: "/resume-screening", icon: FileUp },
  { label: "Schedule", href: "/schedule", icon: MessagesSquare },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
];

export function QuickActions() {
  return (
    <Card>
      <CardContent className="grid grid-cols-2 gap-3 p-5 sm:grid-cols-4">
        {ACTIONS.map((action) => (
          <Link
            key={action.href}
            href={action.href}
            prefetch
            className="flex flex-col items-center justify-center gap-2 rounded-xl border border-border p-4 text-center transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-card"
          >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
                <action.icon className="h-5 w-5 text-primary" />
              </div>
            <span className="text-xs font-medium text-heading">{action.label}</span>
          </Link>
        ))}
      </CardContent>
    </Card>
  );
}
