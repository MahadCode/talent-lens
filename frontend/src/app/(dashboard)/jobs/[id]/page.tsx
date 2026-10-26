"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, Pencil, Trash2, Users } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { CandidateStatusBadge } from "@/components/candidates/candidate-status-badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useJob, useDeleteJob, useUpdateJob } from "@/lib/hooks/use-jobs";
import { useCandidatesForJob } from "@/lib/hooks/use-candidates";
import { getApiErrorMessage } from "@/lib/api/client";
import { formatDate, getInitials } from "@/lib/utils/cn";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = React.useState(false);

  const { data: job, isLoading } = useJob(params.id);
  const { data: candidates, isLoading: candidatesLoading } = useCandidatesForJob(params.id);
  const deleteJob = useDeleteJob();
  const updateJob = useUpdateJob(params.id);

  async function handleDelete() {
    try {
      await deleteJob.mutateAsync(params.id);
      toast.success("Job deleted.");
      router.push("/jobs");
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  if (isLoading || !job) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 rounded-2xl" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Link href="/jobs" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-heading">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to jobs
      </Link>

      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight text-heading">{job.title}</h1>
            <Badge variant={job.status === "OPEN" ? "success" : "secondary"}>{job.status}</Badge>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Posted {formatDate(job.created_at)}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" size="sm">
            <Link href={`/jobs/${job.id}/edit`}>
              <Pencil className="h-3.5 w-3.5" /> Edit
            </Link>
          </Button>
          <Button
            variant="outline"
            size="sm"
            isLoading={updateJob.isPending}
            onClick={async () => {
              try {
                await updateJob.mutateAsync({ status: job.status === "OPEN" ? "CLOSED" : "OPEN" });
                toast.success(job.status === "OPEN" ? "Job closed." : "Job reopened.");
              } catch (error) {
                toast.error(getApiErrorMessage(error));
              }
            }}
          >
            {job.status === "OPEN" ? "Close" : "Reopen"}
          </Button>
        <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
          <DialogTrigger asChild>
            <Button variant="destructive" size="sm">
              <Trash2 className="h-3.5 w-3.5" /> Delete Job
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete this job?</DialogTitle>
              <DialogDescription>
                This will permanently delete &quot;{job.title}&quot; and all associated candidates. This
                action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setDeleteOpen(false)}>
                Cancel
              </Button>
              <Button variant="destructive" isLoading={deleteJob.isPending} onClick={handleDelete}>
                Delete permanently
              </Button>
            </div>
          </DialogContent>
        </Dialog>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Description</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                {job.description}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Requirements</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                {job.requirements}
              </p>
            </CardContent>
          </Card>
          {job.extracted_requirements ? (
            <Card>
              <CardHeader>
                <CardTitle>Extracted skills</CardTitle>
                <CardDescription>Saved from the last extract-requirements run.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p>Required: {(job.extracted_requirements.required_skills ?? []).join(", ") || "—"}</p>
                <p>Preferred: {(job.extracted_requirements.preferred_skills ?? []).join(", ") || "—"}</p>
                <p>Experience: {job.extracted_requirements.experience || "—"}</p>
              </CardContent>
            </Card>
          ) : null}
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Candidates</CardTitle>
            <CardDescription>{candidates?.length ?? 0} candidates evaluated for this role.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-1">
            {candidatesLoading ? (
              Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 rounded-xl" />)
            ) : !candidates || candidates.length === 0 ? (
              <EmptyState
                icon={Users}
                title="No candidates yet"
                description="Upload a resume for this job to start the AI evaluation."
                actionLabel="Upload resume"
                onAction={() => router.push("/resume-screening")}
              />
            ) : (
              candidates.map((candidate) => (
                <Link
                  key={candidate.id}
                  href={`/candidates/${candidate.id}`}
                  className="flex items-center gap-3 rounded-xl px-2 py-2.5 transition-colors hover:bg-muted"
                >
                  <Avatar>
                    <AvatarFallback>{getInitials(candidate.full_name)}</AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-heading">
                      {candidate.full_name ?? "Unnamed candidate"}
                    </p>
                  </div>
                  <CandidateStatusBadge status={candidate.status} />
                </Link>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
