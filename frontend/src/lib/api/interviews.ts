import { apiClient } from "@/lib/api/client";
import type { InterviewEvaluateResponse, InterviewQuestionResponse } from "@/types/domain";

/** Service layer for interview endpoints (`/interview/*`). */
export const interviewsApi = {
  async nextQuestion(params: {
    candidateId: string;
    jobDescription: string;
    conversationHistory: string[];
  }): Promise<InterviewQuestionResponse> {
    const { data } = await apiClient.post<InterviewQuestionResponse>("/interview/questions", {
      candidate_id: params.candidateId,
      job_description: params.jobDescription,
      conversation_history: params.conversationHistory,
    });
    return data;
  },

  async evaluate(params: {
    candidateId: string;
    questionsAndAnswers: string[];
  }): Promise<InterviewEvaluateResponse> {
    const { data } = await apiClient.post<InterviewEvaluateResponse>("/interview/evaluate", {
      candidate_id: params.candidateId,
      questions_and_answers: params.questionsAndAnswers,
    });
    return data;
  },
};
