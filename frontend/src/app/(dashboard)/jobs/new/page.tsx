"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useCreateJob } from "@/lib/hooks/use-jobs";
import { getApiErrorMessage } from "@/lib/api/client";

const schema = z.object({
  title: z.string().min(1, "Job title is required."),
  description: z.string().min(20, "Description should be at least 20 characters."),
  requirements: z.string().min(10, "Requirements should be at least 10 characters."),
});

type FormValues = z.infer<typeof schema>;

export default function NewJobPage() {
  const router = useRouter();
  const createJob = useCreateJob();
  const [skills, setSkills] = React.useState<string[]>([]);
  const [skillInput, setSkillInput] = React.useState("");

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const requirementsValue = watch("requirements") ?? "";

  function addSkill() {
    const trimmed = skillInput.trim();
    if (trimmed && !skills.includes(trimmed)) {
      const next = [...skills, trimmed];
      setSkills(next);
      setValue("requirements", [requirementsValue, trimmed].filter(Boolean).join(", "));
    }
    setSkillInput("");
  }

  function removeSkill(skill: string) {
    setSkills(skills.filter((s) => s !== skill));
  }

  async function onSubmit(values: FormValues) {
    try {
      const job = await createJob.mutateAsync({ ...values, status: "OPEN" });
      toast.success("Job published.");
      router.push(`/jobs/${job.id}`);
    } catch (error) {
      toast.error(getApiErrorMessage(error));
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="label-mono text-muted-foreground">Publish</p>
        <h1 className="mt-1 text-3xl font-normal tracking-tight text-heading">Create a job</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Define the role. Talent Lens matches and scores applicants against this text.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Job details</CardTitle>
          <CardDescription>Give your AI agents everything they need to evaluate applicants well.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-1.5">
              <Label htmlFor="title">Job title</Label>
              <Input id="title" placeholder="Senior Backend Engineer" {...register("title")} />
              {errors.title && <p className="text-xs text-error">{errors.title.message}</p>}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="description">Description</Label>
                <span className="label-mono text-muted-foreground">Free text</span>
              </div>
              <textarea
                id="description"
                rows={6}
                placeholder="We're looking for an experienced backend engineer to..."
                className="w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-heading placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                {...register("description")}
              />
              {errors.description && <p className="text-xs text-error">{errors.description.message}</p>}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="skills">Required skills</Label>
              <div className="flex gap-2">
                <Input
                  id="skills"
                  placeholder="e.g. PostgreSQL — press Enter to add"
                  value={skillInput}
                  onChange={(e) => setSkillInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addSkill();
                    }
                  }}
                />
                <Button type="button" variant="secondary" onClick={addSkill}>
                  Add
                </Button>
              </div>
              {skills.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {skills.map((skill) => (
                    <Badge key={skill} variant="secondary" className="gap-1 pr-1">
                      {skill}
                      <button
                        type="button"
                        onClick={() => removeSkill(skill)}
                        className="rounded-full p-0.5 hover:bg-border/60"
                        aria-label={`Remove ${skill}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="requirements">Full requirements</Label>
              <textarea
                id="requirements"
                rows={4}
                placeholder="5+ years Python, PostgreSQL, distributed systems experience..."
                className="w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-heading placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
                {...register("requirements")}
              />
              {errors.requirements && <p className="text-xs text-error">{errors.requirements.message}</p>}
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <Button type="button" variant="outline" onClick={() => router.back()}>
                Cancel
              </Button>
              <Button type="submit" isLoading={createJob.isPending}>
                Publish job
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
