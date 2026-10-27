import { apiClient } from "@/lib/api/client";
import type { AnalyticsSummary, JobAnalytics } from "@/types/domain";

export const analyticsApi = {
  async summary(): Promise<AnalyticsSummary> {
    const { data } = await apiClient.get<AnalyticsSummary>("/analytics/summary");
    return data;
  },

  async jobReport(jobId: string): Promise<JobAnalytics> {
    const { data } = await apiClient.get<JobAnalytics>(`/analytics/jobs/${jobId}`);
    return data;
  },
};
