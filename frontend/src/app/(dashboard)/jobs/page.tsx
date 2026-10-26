"use client";

import * as React from "react";
import Link from "next/link";
import { Briefcase, Plus, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useJobs } from "@/lib/hooks/use-jobs";
import { formatDate } from "@/lib/utils/cn";
import type { JobStatus } from "@/types/domain";

const STATUS_VARIANT: Record<JobStatus, "outline" | "success" | "secondary" | "warning"> = {
  DRAFT: "outline",
  OPEN: "success",
  CLOSED: "secondary",
  ARCHIVED: "warning",
};

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = React.useState<JobStatus | "ALL">("ALL");
  const [search, setSearch] = React.useState("");

  const { data: jobs, isPending } = useJobs(statusFilter === "ALL" ? undefined : statusFilter);

  const filteredJobs = (jobs ?? []).filter((job) => job.title.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="label-mono text-muted-foreground">Roles</p>
          <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">Jobs</h1>
          <p className="mt-1 text-sm text-muted-foreground">Publish vacancies and track applicant flow.</p>
        </div>
        <Button asChild size="lg">
          <Link href="/jobs/new">
            <Plus className="h-4 w-4" /> New Job
          </Link>
        </Button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search jobs by title..."
            className="pl-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as JobStatus | "ALL")}>
          <SelectTrigger className="sm:w-48">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All statuses</SelectItem>
            <SelectItem value="DRAFT">Draft</SelectItem>
            <SelectItem value="OPEN">Open</SelectItem>
            <SelectItem value="CLOSED">Closed</SelectItem>
            <SelectItem value="ARCHIVED">Archived</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {isPending && !jobs ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-2xl" />
          ))}
        </div>
      ) : filteredJobs.length === 0 ? (
        <EmptyState
          icon={Briefcase}
          title="No jobs found"
          description="Create your first job posting to start receiving AI-screened candidates."
          actionLabel="Create a job"
          onAction={() => (window.location.href = "/jobs/new")}
        />
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filteredJobs.map((job) => (
            <div key={job.id}>
              <Link href={`/jobs/${job.id}`} prefetch>
                <Card className="h-full transition-shadow hover:shadow-soft">
                  <CardContent className="flex h-full flex-col gap-3 p-5">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-base font-semibold text-heading">{job.title}</h3>
                      <Badge variant={STATUS_VARIANT[job.status]}>{job.status}</Badge>
                    </div>
                    <p className="line-clamp-3 flex-1 text-sm text-muted-foreground">{job.description}</p>
                    <p className="text-xs text-muted-foreground">Posted {formatDate(job.created_at)}</p>
                  </CardContent>
                </Card>
              </Link>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
