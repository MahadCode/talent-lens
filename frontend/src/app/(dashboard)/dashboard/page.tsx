"use client";

import { Briefcase, Users, MessagesSquare, UserCheck } from "lucide-react";

import { StatCard } from "@/components/dashboard/stat-card";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/hooks/use-auth";
import { useAnalyticsSummary } from "@/lib/hooks/use-analytics";

export default function DashboardPage() {
  const { user } = useAuth();
  const { data, isPending } = useAnalyticsSummary();
  const firstName = user?.full_name?.split(" ")[0] ?? "there";

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Overview</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight">Welcome back, {firstName}</h1>
        <p className="mt-1 text-sm text-muted-foreground">Live counts from the hiring pipeline. Nothing here is sample data.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {isPending || !data ? (
          Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-[100px]" />)
        ) : (
          <>
            <StatCard label="Active jobs" value={String(data.active_jobs)} icon={Briefcase} />
            <StatCard label="Applications" value={String(data.applications)} icon={Users} />
            <StatCard label="Shortlisted" value={String(data.shortlisted)} icon={UserCheck} />
            <StatCard label="Pending review" value={String(data.pending_reviews)} icon={Users} />
            <StatCard label="Upcoming interviews" value={String(data.upcoming_interviews)} icon={MessagesSquare} />
          </>
        )}
      </div>

      <QuickActions />
    </div>
  );
}
