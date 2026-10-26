"use client";

import { useQuery } from "@tanstack/react-query";
import { analyticsApi } from "@/lib/api/analytics";

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: ["analytics", "summary"],
    queryFn: () => analyticsApi.summary(),
  });
}

export function useJobAnalytics(jobId: string) {
  return useQuery({
    queryKey: ["analytics", "job", jobId],
    queryFn: () => analyticsApi.jobReport(jobId),
    enabled: Boolean(jobId),
  });
}
