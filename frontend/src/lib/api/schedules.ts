import { apiClient } from "@/lib/api/client";
import type { HiringDecision, InterviewType, ScheduledInterview } from "@/types/domain";

export interface ScheduleCreatePayload {
  candidate_id: string;
  scheduled_at: string;
  interviewer_name: string;
  interview_type: InterviewType;
  notes?: string;
}

export const schedulesApi = {
  async create(payload: ScheduleCreatePayload): Promise<ScheduledInterview> {
    const { data } = await apiClient.post<ScheduledInterview>("/interviews", payload);
    return data;
  },

  async list(params?: { from?: string; to?: string; candidate_id?: string }): Promise<ScheduledInterview[]> {
    const { data } = await apiClient.get<ScheduledInterview[]>("/interviews", { params });
    return data;
  },

  async saveFeedback(
    interviewId: string,
    payload: { ratings?: Record<string, number>; comments?: string },
  ): Promise<ScheduledInterview> {
    const { data } = await apiClient.post<ScheduledInterview>(`/interviews/${interviewId}/feedback`, payload);
    return data;
  },

  async recordDecision(interviewId: string, decision: HiringDecision): Promise<ScheduledInterview> {
    const { data } = await apiClient.post<ScheduledInterview>(`/interviews/${interviewId}/decision`, { decision });
    return data;
  },
};
