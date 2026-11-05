"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jobsApi, type JobCreatePayload, type JobUpdatePayload } from "@/lib/api/jobs";
import type { JobStatus } from "@/types/domain";

export function useJobs(status?: JobStatus) {
  return useQuery({
    queryKey: ["jobs", { status }],
    queryFn: () => jobsApi.list({ status }),
  });
}

export function useOpenJobs() {
  return useQuery({
    queryKey: ["jobs", "open"],
    queryFn: () => jobsApi.listOpen(),
  });
}

export function useJob(jobId: string) {
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => jobsApi.get(jobId),
    enabled: Boolean(jobId),
  });
}

export function useCreateJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: JobCreatePayload) => jobsApi.create(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useUpdateJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: JobUpdatePayload) => jobsApi.update(jobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
    },
  });
}

export function useDeleteJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) => jobsApi.remove(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });
}

export function useExtractRequirements(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (apply: boolean) => jobsApi.extractRequirements(jobId, apply),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
    },
  });
}
