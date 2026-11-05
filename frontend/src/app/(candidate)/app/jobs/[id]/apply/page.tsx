"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ResumeDropzone } from "@/components/shared/resume-dropzone";
import { useJob } from "@/lib/hooks/use-jobs";
import { useApplyToJob } from "@/lib/hooks/use-candidates";
import { getApiErrorMessage } from "@/lib/api/client";

export default function ApplyPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { data: job } = useJob(params.id);
  const apply = useApplyToJob();
  const [file, setFile] = React.useState<File | null>(null);

  async function onSubmit() {
    if (!file) {
      toast.error("Choose a PDF resume first.");
      return;
    }
    try {
      const result = await apply.mutateAsync({ jobId: params.id, file });
      toast.success("Application submitted.");
      router.push(`/app/applications/${result.candidate_id}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <Link
        href={`/app/jobs/${params.id}`}
        className="label-mono inline-flex items-center gap-2 text-muted-foreground hover:text-heading"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back
      </Link>
      <div>
        <p className="label-mono text-muted-foreground">Apply</p>
        <h1 className="mt-1 text-3xl font-normal">{job?.title ?? "Open role"}</h1>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Upload your resume</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ResumeDropzone file={file} onFileSelected={setFile} disabled={apply.isPending} />
          <Button className="w-full" onClick={() => void onSubmit()} isLoading={apply.isPending}>
            Submit application
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
