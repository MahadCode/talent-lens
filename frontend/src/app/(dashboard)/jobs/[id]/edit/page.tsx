"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useExtractRequirements, useJob, useUpdateJob } from "@/lib/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api/client";
import type { ExtractedRequirements } from "@/types/domain";

export default function EditJobPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { data: job } = useJob(params.id);
  const updateJob = useUpdateJob(params.id);
  const extract = useExtractRequirements(params.id);
  const [preview, setPreview] = React.useState<ExtractedRequirements | null>(null);

  const form = useForm({
    values: {
      title: job?.title ?? "",
      description: job?.description ?? "",
      requirements: job?.requirements ?? "",
    },
  });

  async function onSubmit(values: { title: string; description: string; requirements: string }) {
    try {
      await updateJob.mutateAsync(values);
      toast.success("Job updated.");
      router.push(`/jobs/${params.id}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Jobs</p>
        <h1 className="mt-1 text-3xl font-normal">Edit job</h1>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Role copy</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-1.5">
              <Label>Title</Label>
              <Input {...form.register("title")} />
            </div>
            <div className="space-y-1.5">
              <Label>Description</Label>
              <textarea className="w-full border border-heading/15 bg-surface px-3 py-2 text-sm" rows={6} {...form.register("description")} />
            </div>
            <div className="space-y-1.5">
              <Label>Requirements</Label>
              <textarea className="w-full border border-heading/15 bg-surface px-3 py-2 text-sm" rows={4} {...form.register("requirements")} />
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                variant="outline"
                isLoading={extract.isPending}
                onClick={async () => {
                  try {
                    const result = await extract.mutateAsync(false);
                    setPreview(result);
                    toast.success("Requirements extracted. Review, then apply.");
                  } catch (error) {
                    toast.error(getApiErrorMessage(error));
                  }
                }}
              >
                Extract from text
              </Button>
              {preview ? (
                <Button
                  type="button"
                  variant="outline"
                  onClick={async () => {
                    try {
                      await extract.mutateAsync(true);
                      toast.success("Saved on the job.");
                    } catch (error) {
                      toast.error(getApiErrorMessage(error));
                    }
                  }}
                >
                  Save extraction
                </Button>
              ) : null}
              <Button type="submit" isLoading={updateJob.isPending}>
                Save job
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      {preview ? (
        <Card>
          <CardHeader>
            <CardTitle>Extracted skills</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Required: {(preview.required_skills ?? []).join(", ") || "—"}</p>
            <p>Preferred: {(preview.preferred_skills ?? []).join(", ") || "—"}</p>
            <p>Experience: {preview.experience || "—"}</p>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
