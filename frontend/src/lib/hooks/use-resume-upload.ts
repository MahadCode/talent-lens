"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { resumesApi } from "@/lib/api/resumes";

export function useResumeUpload() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: resumesApi.upload,
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "by-job", variables.jobId] });
    },
  });
}
