import { apiClient } from "@/lib/api/client";
import type { ExtractedRequirements, Job, JobStatus } from "@/types/domain";

export interface JobCreatePayload {
  title: string;
  description: string;
  requirements: string;
  status?: JobStatus;
}

export type JobUpdatePayload = Partial<JobCreatePayload>;

export const jobsApi = {
  async list(params?: { status?: JobStatus; offset?: number; limit?: number }): Promise<Job[]> {
    const { data } = await apiClient.get<Job[]>("/jobs", { params });
    return data;
  },

  async listOpen(params?: { offset?: number; limit?: number }): Promise<Job[]> {
    const { data } = await apiClient.get<Job[]>("/jobs/open", { params });
    return data;
  },

  async get(jobId: string): Promise<Job> {
    const { data } = await apiClient.get<Job>(`/jobs/${jobId}`);
    return data;
  },

  async create(payload: JobCreatePayload): Promise<Job> {
    const { data } = await apiClient.post<Job>("/jobs", payload);
    return data;
  },

  async update(jobId: string, payload: JobUpdatePayload): Promise<Job> {
    const { data } = await apiClient.put<Job>(`/jobs/${jobId}`, payload);
    return data;
  },

  async remove(jobId: string): Promise<void> {
    await apiClient.delete(`/jobs/${jobId}`);
  },

  async extractRequirements(
    jobId: string,
    apply: boolean,
  ): Promise<ExtractedRequirements & { applied: boolean }> {
    const { data } = await apiClient.post(`/jobs/${jobId}/extract-requirements`, { apply });
    return data;
  },
};
