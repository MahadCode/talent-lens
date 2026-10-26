"use client";

import * as React from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { StatCard } from "@/components/dashboard/stat-card";
import { useAnalyticsSummary, useJobAnalytics } from "@/lib/hooks/use-analytics";
import { useJobs } from "@/lib/hooks/use-jobs";
import { Clock, Percent, Target, Users } from "lucide-react";

export default function AnalyticsPage() {
  const { data: summary } = useAnalyticsSummary();
  const { data: jobs } = useJobs();
  const [jobId, setJobId] = React.useState("");
  const { data: report } = useJobAnalytics(jobId);

  const stageData = report
    ? Object.entries(report.counts_by_status).map(([status, count]) => ({ status, count }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Reports</p>
        <h1 className="mt-1 text-3xl font-normal">Analytics</h1>
        <p className="mt-1 text-sm text-muted-foreground">Figures come from the live pipeline, not placeholders.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Active jobs" value={String(summary?.active_jobs ?? 0)} icon={Target} />
        <StatCard label="Applications" value={String(summary?.applications ?? 0)} icon={Users} />
        <StatCard label="Shortlisted" value={String(summary?.shortlisted ?? 0)} icon={Percent} />
        <StatCard label="Upcoming interviews" value={String(summary?.upcoming_interviews ?? 0)} icon={Clock} />
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>Job report</CardTitle>
              <CardDescription>Stage counts, shortlist rate, processing time, skill gaps.</CardDescription>
            </div>
            <Select value={jobId} onValueChange={setJobId}>
              <SelectTrigger className="sm:w-64">
                <SelectValue placeholder="Select a job" />
              </SelectTrigger>
              <SelectContent>
                {(jobs ?? []).map((job) => (
                  <SelectItem key={job.id} value={job.id}>{job.title}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {!report ? (
            <p className="text-sm text-muted-foreground">Pick a job to load its report.</p>
          ) : (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <p className="text-sm">Shortlist rate <strong>{Math.round(report.application_to_shortlist_rate * 100)}%</strong></p>
                <p className="text-sm">Avg. processing hours <strong>{report.average_processing_hours ?? "—"}</strong></p>
                <p className="text-sm">Common gaps <strong>{report.common_skill_gaps.map((g) => g.skill).join(", ") || "—"}</strong></p>
              </div>
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stageData}>
                    <CartesianGrid stroke="rgba(20,20,20,.09)" vertical={false} />
                    <XAxis dataKey="status" tick={{ fontSize: 11 }} />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#ff8a3d" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
