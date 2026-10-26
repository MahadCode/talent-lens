"use client";

import type { LucideIcon } from "lucide-react";
import { ArrowUpRight, ArrowDownRight } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils/cn";

interface StatCardProps {
  label: string;
  value: string;
  icon: LucideIcon;
  trend?: { value: number; positive: boolean };
  accent?: "primary" | "secondary" | "accent";
}

const ACCENT_CLASSES: Record<NonNullable<StatCardProps["accent"]>, string> = {
  primary: "bg-primary/10 text-primary",
  secondary: "bg-secondary/10 text-secondary",
  accent: "bg-accent/15 text-accent",
};

export function StatCard({ label, value, icon: Icon, trend, accent = "primary" }: StatCardProps) {
  return (
    <Card className="hover:shadow-soft">
      <CardContent className="flex items-start justify-between p-5">
        <div className="space-y-1.5">
          <p className="label-mono text-muted-foreground">{label}</p>
          <p className="text-2xl font-normal tracking-tight text-heading">{value}</p>
          {trend && (
            <span
              className={cn(
                "inline-flex items-center gap-0.5 text-xs font-medium",
                trend.positive ? "text-success" : "text-error",
              )}
            >
              {trend.positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
              {trend.value}% vs last week
            </span>
          )}
        </div>
        <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-xl", ACCENT_CLASSES[accent])}>
          <Icon className="h-5 w-5" />
        </div>
      </CardContent>
    </Card>
  );
}
