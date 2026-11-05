"use client";

import Link from "next/link";
import { Briefcase } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { Skeleton } from "@/components/ui/skeleton";
import { useOpenJobs } from "@/lib/hooks/use-jobs";
import { formatDate } from "@/lib/utils/cn";

export default function OpenJobsPage() {
  const { data: jobs, isLoading } = useOpenJobs();

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Vacancies</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight">Open jobs</h1>
        <p className="mt-1 text-sm text-muted-foreground">Apply with a PDF resume. You will only see your own status.</p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      ) : !jobs?.length ? (
        <EmptyState icon={Briefcase} title="No open roles" description="Check back when a recruiter publishes a vacancy." />
      ) : (
        <div className="space-y-3">
          {jobs.map((job) => (
            <Link key={job.id} href={`/app/jobs/${job.id}`}>
              <Card className="transition-colors hover:bg-heading/5">
                <CardContent className="flex items-start justify-between gap-4 p-6">
                  <div>
                    <p className="label-mono text-muted-foreground">{job.status}</p>
                    <h2 className="mt-1 text-xl">{job.title}</h2>
                    <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{job.description}</p>
                  </div>
                  <p className="label-mono shrink-0 text-muted-foreground">{formatDate(job.created_at)}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
