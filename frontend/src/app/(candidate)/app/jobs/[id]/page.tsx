"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useJob } from "@/lib/hooks/use-jobs";
import { useMyApplications } from "@/lib/hooks/use-candidates";

export default function CandidateJobPage() {
  const params = useParams<{ id: string }>();
  const { data: job, isLoading } = useJob(params.id);
  const { data: mine } = useMyApplications();
  const existing = mine?.find((application) => application.job_id === params.id);

  if (isLoading || !job) {
    return <Skeleton className="h-64" />;
  }

  return (
    <div className="space-y-6">
      <Link href="/app" className="label-mono inline-flex items-center gap-2 text-muted-foreground hover:text-heading">
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </Link>
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="label-mono text-muted-foreground">{job.status}</p>
          <h1 className="mt-1 text-3xl font-normal">{job.title}</h1>
        </div>
        {existing ? (
          <Button asChild variant="outline">
            <Link href={`/app/applications/${existing.id}`}>View application · {existing.status}</Link>
          </Button>
        ) : (
          <Button asChild>
            <Link href={`/app/jobs/${job.id}/apply`}>Apply with PDF</Link>
          </Button>
        )}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Description</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">{job.description}</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Requirements</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">{job.requirements}</p>
        </CardContent>
      </Card>
    </div>
  );
}
