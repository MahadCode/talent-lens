"use client";

import Link from "next/link";
import { FolderOpen } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { EmptyState } from "@/components/shared/empty-state";
import { CandidateStatusBadge } from "@/components/candidates/candidate-status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyApplications } from "@/lib/hooks/use-candidates";
import { formatDate } from "@/lib/utils/cn";

export default function MyApplicationsPage() {
  const { data, isLoading } = useMyApplications();

  return (
    <div className="space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Pipeline</p>
        <h1 className="mt-1 text-3xl font-normal">My applications</h1>
      </div>
      {isLoading ? (
        <Skeleton className="h-32" />
      ) : !data?.length ? (
        <EmptyState
          icon={FolderOpen}
          title="No applications yet"
          description="Browse open jobs and apply with a PDF."
          actionLabel="Open jobs"
          onAction={() => {
            window.location.href = "/app";
          }}
        />
      ) : (
        <div className="space-y-2">
          {data.map((application) => (
            <Link key={application.id} href={`/app/applications/${application.id}`}>
              <Card className="hover:bg-heading/5">
                <CardContent className="flex items-center justify-between gap-4 p-5">
                  <div>
                    <h2 className="text-lg">{application.job_title ?? "Untitled role"}</h2>
                    <p className="label-mono mt-1 text-muted-foreground">{formatDate(application.created_at)}</p>
                  </div>
                  <CandidateStatusBadge status={application.status} />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
