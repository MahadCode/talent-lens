"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CandidateStatusBadge } from "@/components/candidates/candidate-status-badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyApplication } from "@/lib/hooks/use-candidates";

export default function MyApplicationDetailPage() {
  const params = useParams<{ id: string }>();
  const { data, isLoading } = useMyApplication(params.id);
  const profile = data?.parsed_profile;

  if (isLoading || !data) {
    return <Skeleton className="h-64" />;
  }

  return (
    <div className="space-y-6">
      <Link href="/app/applications" className="label-mono inline-flex items-center gap-2 text-muted-foreground hover:text-heading">
        <ArrowLeft className="h-3.5 w-3.5" /> Applications
      </Link>
      <div className="flex items-center gap-3">
        <h1 className="text-3xl font-normal">{data.job_title ?? "Application"}</h1>
        <CandidateStatusBadge status={data.status} />
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Parsed skills</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-1.5">
          {profile?.skills?.length ? (
            profile.skills.map((skill) => (
              <Badge key={skill} variant="outline">
                {skill}
              </Badge>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No skills extracted yet.</p>
          )}
        </CardContent>
      </Card>
      <p className="text-sm text-muted-foreground">
        Recruiters review your application privately. You will only see status changes here.
      </p>
    </div>
  );
}
