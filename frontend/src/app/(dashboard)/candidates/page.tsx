"use client";

import * as React from "react";
import Link from "next/link";
import { Users } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CandidateStatusBadge } from "@/components/candidates/candidate-status-badge";
import { useJobs } from "@/lib/hooks/use-jobs";
import { useCandidatesForJob } from "@/lib/hooks/use-candidates";
import { getInitials } from "@/lib/utils/cn";

export default function CandidatesPage() {
  const { data: jobs, isPending: jobsPending } = useJobs();
  const [selectedJobId, setSelectedJobId] = React.useState<string>("");

  React.useEffect(() => {
    if (!selectedJobId && jobs && jobs.length > 0) {
      setSelectedJobId(jobs[0]!.id);
    }
  }, [jobs, selectedJobId]);

  const { data: candidates, isPending: candidatesPending } = useCandidatesForJob(selectedJobId);

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="label-mono text-muted-foreground">Pipeline</p>
          <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">Candidates</h1>
          <p className="mt-1 text-sm text-muted-foreground">Browse scored applicants by job.</p>
        </div>

        {jobsPending && !jobs ? (
          <Skeleton className="h-10 w-64 rounded-xl" />
        ) : (
          <Select value={selectedJobId} onValueChange={setSelectedJobId}>
            <SelectTrigger className="sm:w-64">
              <SelectValue placeholder="Select a job" />
            </SelectTrigger>
            <SelectContent>
              {(jobs ?? []).map((job) => (
                <SelectItem key={job.id} value={job.id}>
                  {job.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {candidatesPending && !candidates ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      ) : !candidates || candidates.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No candidates for this job"
          description="Once resumes are uploaded and parsed for this job, candidates will show up here."
        />
      ) : (
        <Card>
          <CardContent className="divide-y divide-border p-0">
            {candidates.map((candidate) => (
              <div key={candidate.id}>
                <Link
                  href={`/candidates/${candidate.id}`}
                  prefetch
                  className="flex items-center gap-4 px-5 py-4 transition-colors hover:bg-muted"
                >
                  <Avatar className="h-10 w-10">
                    <AvatarFallback>{getInitials(candidate.full_name)}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-heading">
                      {candidate.full_name ?? "Unnamed candidate"}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {candidate.email ?? "No email parsed yet"}
                    </p>
                  </div>
                  {candidate.match_percentage != null && (
                    <Badge variant="secondary">{Math.round(candidate.match_percentage)}% match</Badge>
                  )}
                  <CandidateStatusBadge status={candidate.status} />
                </Link>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
