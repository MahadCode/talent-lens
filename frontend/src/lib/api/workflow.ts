import { apiClient } from "@/lib/api/client";
import type { WorkflowEvaluateResponse } from "@/types/domain";

/** Service layer for the LangGraph evaluation workflow (`/workflow/*`). */
export const workflowApi = {
  async evaluate(params: { candidateId: string; githubSummary?: string }): Promise<WorkflowEvaluateResponse> {
    const { data } = await apiClient.post<WorkflowEvaluateResponse>("/workflow/evaluate", {
      candidate_id: params.candidateId,
      github_summary: params.githubSummary,
    });
    return data;
  },
};
