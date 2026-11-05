import { apiClient } from "@/lib/api/client";
import type {
  Assessment,
  Candidate,
  CandidateApplication,
  CandidateNote,
  CandidateStatus,
  QuestionSet,
  StatusEvent,
  StoredQuestion,
} from "@/types/domain";
import type { ResumeUploadResponse } from "@/lib/api/resumes";

export const candidatesApi = {
  async listForJob(jobId: string, params?: { offset?: number; limit?: number }): Promise<Candidate[]> {
    const { data } = await apiClient.get<Candidate[]>("/candidates", { params: { job_id: jobId, ...params } });
    return data;
  },

  async get(candidateId: string): Promise<Candidate> {
    const { data } = await apiClient.get<Candidate>(`/candidates/${candidateId}`);
    return data;
  },

  async getAssessment(candidateId: string): Promise<Assessment> {
    const { data } = await apiClient.get<Assessment>(`/candidates/${candidateId}/assessment`);
    return data;
  },

  async changeStatus(candidateId: string, status: CandidateStatus): Promise<Candidate> {
    const { data } = await apiClient.patch<Candidate>(`/candidates/${candidateId}/status`, { status });
    return data;
  },

  async addNote(candidateId: string, body: string): Promise<CandidateNote> {
    const { data } = await apiClient.post<CandidateNote>(`/candidates/${candidateId}/notes`, { body });
    return data;
  },

  async listNotes(candidateId: string): Promise<CandidateNote[]> {
    const { data } = await apiClient.get<CandidateNote[]>(`/candidates/${candidateId}/notes`);
    return data;
  },

  async listEvents(candidateId: string): Promise<StatusEvent[]> {
    const { data } = await apiClient.get<StatusEvent[]>(`/candidates/${candidateId}/events`);
    return data;
  },

  async updateProfile(
    candidateId: string,
    payload: Partial<{ skills: string[]; experience: string[]; projects: string[]; education: string[]; certifications: string[] }>,
  ): Promise<Candidate> {
    const { data } = await apiClient.patch<Candidate>(`/candidates/${candidateId}/profile`, payload);
    return data;
  },

  async overrideScore(candidateId: string, totalScore: number, reason: string): Promise<Candidate> {
    const { data } = await apiClient.patch<Candidate>(`/candidates/${candidateId}/score`, {
      total_score: totalScore,
      reason,
    });
    return data;
  },

  async apply(jobId: string, file: File): Promise<ResumeUploadResponse> {
    const formData = new FormData();
    formData.append("job_id", jobId);
    formData.append("file", file);
    const { data } = await apiClient.post<ResumeUploadResponse>("/candidates/apply", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  async listMine(): Promise<CandidateApplication[]> {
    const { data } = await apiClient.get<CandidateApplication[]>("/candidates/me");
    return data;
  },

  async getMine(candidateId: string): Promise<CandidateApplication> {
    const { data } = await apiClient.get<CandidateApplication>(`/candidates/me/${candidateId}`);
    return data;
  },

  async updateMyProfile(
    candidateId: string,
    payload: Partial<{ skills: string[]; experience: string[]; projects: string[]; education: string[]; certifications: string[] }>,
  ): Promise<CandidateApplication> {
    const { data } = await apiClient.patch<CandidateApplication>(`/candidates/me/${candidateId}/profile`, payload);
    return data;
  },

  async generateQuestions(candidateId: string): Promise<QuestionSet> {
    const { data } = await apiClient.post<QuestionSet>(`/candidates/${candidateId}/questions/generate`);
    return data;
  },

  async regenerateQuestions(candidateId: string): Promise<QuestionSet> {
    const { data } = await apiClient.post<QuestionSet>(`/candidates/${candidateId}/questions/regenerate`);
    return data;
  },

  async listQuestions(candidateId: string): Promise<QuestionSet> {
    const { data } = await apiClient.get<QuestionSet>(`/candidates/${candidateId}/questions`);
    return data;
  },

  async updateQuestion(
    questionId: string,
    payload: Partial<Pick<StoredQuestion, "question" | "focus_area" | "difficulty" | "guideline">>,
  ): Promise<StoredQuestion> {
    const { data } = await apiClient.put<StoredQuestion>(`/interview/questions/${questionId}`, payload);
    return data;
  },

  async deleteQuestion(questionId: string): Promise<QuestionSet> {
    const { data } = await apiClient.delete<QuestionSet>(`/interview/questions/${questionId}`);
    return data;
  },
};
